import os
import re
import shutil
import tempfile
import yt_dlp
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import URLSerializer, DownloadSerializer


def detect_platform(url):
    """Detect whether the URL is from YouTube or Instagram."""
    if re.search(r'(youtube\.com|youtu\.be)', url):
        return 'youtube'
    elif re.search(r'(instagram\.com|instagr\.am)', url):
        return 'instagram'
    return 'unknown'


def get_base_ydl_opts():
    """
    Return base yt-dlp options that work on cloud servers.
    Includes user-agent spoofing, geo bypass, and retry logic
    to avoid bot detection on platforms like YouTube.
    """
    return {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'socket_timeout': 30,
        'retries': 5,
        'extractor_retries': 5,
        'noplaylist': True,
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['web'],
            },
        },
    }


def has_ffmpeg():
    """Check if FFmpeg is available on the system."""
    return shutil.which('ffmpeg') is not None


class VideoInfoView(APIView):
    """
    POST: Accepts a URL and returns video metadata + available formats.
    """

    def post(self, request):
        serializer = URLSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        url = serializer.validated_data['url']
        platform = detect_platform(url)

        if platform == 'unknown':
            return Response(
                {"error": "Unsupported platform. Only YouTube and Instagram are supported."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ydl_opts = get_base_ydl_opts()
        ydl_opts['skip_download'] = True

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Build format list
                formats = []
                if info.get('formats'):
                    for f in info['formats']:
                        fmt = {
                            'format_id': f.get('format_id', ''),
                            'ext': f.get('ext', ''),
                            'resolution': f.get('resolution', 'audio only'),
                            'filesize': f.get('filesize') or f.get('filesize_approx'),
                            'vcodec': f.get('vcodec', 'none'),
                            'acodec': f.get('acodec', 'none'),
                            'fps': f.get('fps'),
                            'tbr': f.get('tbr'),
                            'format_note': f.get('format_note', ''),
                        }
                        # Classify as video or audio
                        if f.get('vcodec', 'none') != 'none' and f.get('acodec', 'none') != 'none':
                            fmt['type'] = 'video+audio'
                        elif f.get('vcodec', 'none') != 'none':
                            fmt['type'] = 'video_only'
                        else:
                            fmt['type'] = 'audio_only'
                        formats.append(fmt)

                # Deduplicate and create quality options
                video_formats = []
                audio_formats = []
                seen_resolutions = set()
                seen_audio = set()

                for f in formats:
                    if f['type'] in ('video+audio', 'video_only'):
                        res = f.get('resolution', '')
                        if res and res not in seen_resolutions:
                            seen_resolutions.add(res)
                            video_formats.append(f)
                    elif f['type'] == 'audio_only':
                        tbr = f.get('tbr')
                        key = f"{f.get('ext', '')}_{tbr}"
                        if key not in seen_audio:
                            seen_audio.add(key)
                            audio_formats.append(f)

                # Sort video by resolution (descending), audio by bitrate (descending)
                def get_resolution_height(fmt):
                    res = fmt.get('resolution', '0')
                    match = re.search(r'(\d+)', res)
                    return int(match.group(1)) if match else 0

                video_formats.sort(key=get_resolution_height, reverse=True)
                audio_formats.sort(
                    key=lambda x: x.get('tbr') or 0,
                    reverse=True
                )

                return Response({
                    'title': info.get('title', 'Unknown'),
                    'thumbnail': info.get('thumbnail', ''),
                    'duration': info.get('duration', 0),
                    'platform': platform,
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'video_formats': video_formats,
                    'audio_formats': audio_formats,
                })

        except yt_dlp.utils.DownloadError as e:
            return Response(
                {"error": f"Could not fetch video info: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DownloadVideoView(APIView):
    """
    POST: Accepts a URL, format_id, and download_type (video/audio),
    then streams the file back to the client.
    """

    def post(self, request):
        serializer = DownloadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        url = serializer.validated_data['url']
        format_id = serializer.validated_data.get('format_id', 'best')
        download_type = serializer.validated_data.get('download_type', 'video')
        platform = detect_platform(url)

        if platform == 'unknown':
            return Response(
                {"error": "Unsupported platform."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ffmpeg_available = has_ffmpeg()

        # Create a temp directory for the download
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

        # Start with cloud-friendly base options
        ydl_opts = get_base_ydl_opts()
        ydl_opts['outtmpl'] = output_template

        if download_type == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            if ffmpeg_available:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            if format_id and format_id != 'best':
                ydl_opts['format'] = format_id
        else:
            # Video download
            if ffmpeg_available:
                if format_id and format_id != 'best':
                    ydl_opts['format'] = f'{format_id}+bestaudio/best'
                else:
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'
                ydl_opts['merge_output_format'] = 'mp4'
            else:
                if format_id and format_id != 'best':
                    ydl_opts['format'] = f'{format_id}/best'
                else:
                    ydl_opts['format'] = 'best'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'download')

                # Find the downloaded file
                downloaded_file = None
                for f in os.listdir(temp_dir):
                    filepath = os.path.join(temp_dir, f)
                    if os.path.isfile(filepath):
                        downloaded_file = filepath
                        break

                if not downloaded_file:
                    return Response(
                        {"error": "Download completed but file not found."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                # Determine content type
                ext = os.path.splitext(downloaded_file)[1].lower()
                content_types = {
                    '.mp4': 'video/mp4',
                    '.webm': 'video/webm',
                    '.mkv': 'video/x-matroska',
                    '.mp3': 'audio/mpeg',
                    '.m4a': 'audio/mp4',
                    '.opus': 'audio/opus',
                    '.ogg': 'audio/ogg',
                    '.wav': 'audio/wav',
                }
                content_type = content_types.get(ext, 'application/octet-stream')

                # Clean the title for filename
                safe_title = re.sub(r'[^\w\s\-]', '', title).strip()
                filename = f"{safe_title}{ext}"

                response = FileResponse(
                    open(downloaded_file, 'rb'),
                    content_type=content_type
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['Access-Control-Expose-Headers'] = 'Content-Disposition'
                return response

        except yt_dlp.utils.DownloadError as e:
            return Response(
                {"error": f"Download failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
