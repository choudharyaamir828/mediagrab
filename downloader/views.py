import os
import re
import shutil
import tempfile
import logging
import yt_dlp
from django.conf import settings
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import URLSerializer, DownloadSerializer

logger = logging.getLogger(__name__)


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
    Includes user-agent spoofing, geo bypass, retry logic,
    and multiple player_client fallbacks to avoid bot detection.
    """
    opts = {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'socket_timeout': 60,
        'retries': 10,
        'extractor_retries': 10,
        'fragment_retries': 10,
        'noplaylist': True,
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/131.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': 'https://www.google.com/',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'mweb'],
            },
        },
    }

    # Support optional cookies file for YouTube authentication
    # Set YTDLP_COOKIES_FILE env var to the path of a Netscape-format cookies file
    cookies_file = os.environ.get('YTDLP_COOKIES_FILE')
    if cookies_file and os.path.isfile(cookies_file):
        opts['cookiefile'] = cookies_file
        logger.info("Using cookies file: %s", cookies_file)

    return opts


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
            logger.warning("Invalid request data: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        url = serializer.validated_data['url']
        platform = detect_platform(url)
        logger.info("VideoInfoView: Fetching info for URL=%s, platform=%s", url, platform)

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

            if not info:
                logger.error("yt-dlp returned None for URL: %s", url)
                return Response(
                    {"error": "Could not retrieve video information. The video may be private or unavailable."},
                    status=status.HTTP_400_BAD_REQUEST
                )

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

            logger.info(
                "VideoInfoView: Success for '%s' — %d video formats, %d audio formats",
                info.get('title', 'Unknown'), len(video_formats), len(audio_formats)
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
            error_msg = str(e)
            logger.error("yt-dlp DownloadError for URL %s: %s", url, error_msg)

            # Provide user-friendly messages for common errors
            if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
                user_msg = (
                    "YouTube is blocking this request from our server. "
                    "This is a known limitation with cloud-based downloaders. "
                    "Please try again in a few minutes."
                )
            elif 'Private video' in error_msg or 'private' in error_msg.lower():
                user_msg = "This video is private and cannot be downloaded."
            elif 'unavailable' in error_msg.lower():
                user_msg = "This video is unavailable. It may have been removed or is restricted in your region."
            elif 'is not a valid URL' in error_msg:
                user_msg = "The provided URL is not valid. Please check and try again."
            else:
                user_msg = f"Could not fetch video info: {error_msg}"

            return Response(
                {"error": user_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception("Unexpected error in VideoInfoView for URL %s", url)
            error_msg = str(e)
            return Response(
                {"error": f"An unexpected error occurred: {error_msg}"},
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
            logger.warning("Invalid download request: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        url = serializer.validated_data['url']
        format_id = serializer.validated_data.get('format_id', 'best')
        download_type = serializer.validated_data.get('download_type', 'video')
        platform = detect_platform(url)

        logger.info(
            "DownloadVideoView: url=%s, format_id=%s, type=%s, platform=%s",
            url, format_id, download_type, platform
        )

        if platform == 'unknown':
            return Response(
                {"error": "Unsupported platform."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ffmpeg_available = has_ffmpeg()
        logger.info("FFmpeg available: %s", ffmpeg_available)

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
                    logger.error("Download completed but no file found in %s", temp_dir)
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

                logger.info("Serving file: %s (%s)", filename, content_type)

                response = FileResponse(
                    open(downloaded_file, 'rb'),
                    content_type=content_type
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['Access-Control-Expose-Headers'] = 'Content-Disposition'
                return response

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            logger.error("yt-dlp DownloadError: %s", error_msg)

            if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
                user_msg = (
                    "YouTube is blocking this request from our server. "
                    "Please try again in a few minutes."
                )
            else:
                user_msg = f"Download failed: {error_msg}"

            return Response(
                {"error": user_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception("Unexpected error in DownloadVideoView")
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Clean up temp directory (but not if we're serving a file)
            # The FileResponse will handle the open file handle
            pass


class HealthCheckView(APIView):
    """
    GET: Returns server health + diagnostic info.
    Visit /api/health/ in production to check if everything is working.
    """

    def get(self, request):
        import sys

        ffmpeg_available = has_ffmpeg()
        cookies_file = os.environ.get('YTDLP_COOKIES_FILE', '')
        cookies_exists = os.path.isfile(cookies_file) if cookies_file else False

        return Response({
            'status': 'ok',
            'python_version': sys.version,
            'yt_dlp_version': yt_dlp.version.__version__,
            'ffmpeg_available': ffmpeg_available,
            'cookies_file_configured': bool(cookies_file),
            'cookies_file_exists': cookies_exists,
        })
