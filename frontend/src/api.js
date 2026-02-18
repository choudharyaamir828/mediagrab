import axios from 'axios';

// Use environment variable for production, fallback to localhost for dev
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 180000, // 3 minute timeout — Render spin-up (~30s) + yt-dlp processing
    headers: {
        'Content-Type': 'application/json',
    },
});

/**
 * Fetch video info (metadata + available formats)
 * @param {string} url - YouTube or Instagram URL
 */
export const fetchVideoInfo = async (url) => {
    const response = await api.post('/info/', { url });
    return response.data;
};

/**
 * Download video or audio
 * @param {string} url - YouTube or Instagram URL
 * @param {string} formatId - Format ID from the info response
 * @param {string} downloadType - 'video' or 'audio'
 * @param {Function} onProgress - Progress callback function
 */
export const downloadMedia = async (url, formatId, downloadType, onProgress) => {
    const response = await api.post(
        '/download/',
        { url, format_id: formatId, download_type: downloadType },
        {
            responseType: 'blob',
            onDownloadProgress: (progressEvent) => {
                if (onProgress && progressEvent.total) {
                    const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    onProgress(percent);
                }
            },
        }
    );

    // Extract filename from Content-Disposition header
    const contentDisposition = response.headers['content-disposition'];
    let filename = downloadType === 'audio' ? 'download.mp3' : 'download.mp4';
    if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+?)"/);
        if (match) {
            filename = match[1];
        }
    }

    return { blob: response.data, filename };
};

export default api;
