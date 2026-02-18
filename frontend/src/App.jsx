import { useState, useCallback } from 'react';
import { fetchVideoInfo, downloadMedia } from './api';
import './App.css';

// SVG Icons as components
const LinkIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
  </svg>
);

const DownloadIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

const SearchIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);

const VideoIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="23 7 16 12 23 17 23 7" />
    <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
  </svg>
);

const AudioIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 18V5l12-2v13" />
    <circle cx="6" cy="18" r="3" />
    <circle cx="18" cy="16" r="3" />
  </svg>
);

const XIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const AlertIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

const YouTubeIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor">
    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
  </svg>
);

const InstagramIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z" />
  </svg>
);

const DownloadCloudIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="8 17 12 21 16 17" />
    <line x1="12" y1="12" x2="12" y2="21" />
    <path d="M20.88 18.09A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.29" />
  </svg>
);

function formatDuration(seconds) {
  if (!seconds) return '';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function formatFileSize(bytes) {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function formatViews(count) {
  if (!count) return '';
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M views`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}K views`;
  return `${count} views`;
}

function detectPlatform(url) {
  if (/youtube\.com|youtu\.be/i.test(url)) return 'youtube';
  if (/instagram\.com|instagr\.am/i.test(url)) return 'instagram';
  return null;
}

function App() {
  const [url, setUrl] = useState('');
  const [platform, setPlatform] = useState(null);
  const [downloadType, setDownloadType] = useState('video');
  const [videoInfo, setVideoInfo] = useState(null);
  const [selectedFormat, setSelectedFormat] = useState('best');
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleUrlChange = useCallback((e) => {
    const value = e.target.value;
    setUrl(value);
    setPlatform(detectPlatform(value));
    setError('');
    setSuccess('');
    // Reset info when URL changes
    if (videoInfo) {
      setVideoInfo(null);
      setSelectedFormat('best');
    }
  }, [videoInfo]);

  const clearUrl = () => {
    setUrl('');
    setPlatform(null);
    setVideoInfo(null);
    setSelectedFormat('best');
    setError('');
    setSuccess('');
  };

  const handleFetchInfo = async () => {
    if (!url.trim()) {
      setError('Please enter a valid URL');
      return;
    }
    if (!platform) {
      setError('Only YouTube and Instagram URLs are supported');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    setVideoInfo(null);

    try {
      const info = await fetchVideoInfo(url);
      setVideoInfo(info);
      setSelectedFormat('best');
    } catch (err) {
      let message;
      if (err.response?.data?.error) {
        // Server returned an error with a message
        message = err.response.data.error;
      } else if (err.response) {
        // Server returned an error without a proper message
        message = `Server error (${err.response.status}). Please try again.`;
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        message = 'Request timed out. The server may be busy — please try again.';
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        message = 'Cannot connect to the server. Please check your internet connection or try again later.';
      } else {
        message = 'Failed to fetch video information. Please check the URL.';
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!url.trim()) return;

    setDownloading(true);
    setProgress(0);
    setError('');
    setSuccess('');

    try {
      const { blob, filename } = await downloadMedia(
        url,
        selectedFormat,
        downloadType,
        (percent) => setProgress(percent)
      );

      // Trigger browser download
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setSuccess(`"${videoInfo?.title || 'Media'}" downloaded successfully!`);
      setProgress(100);
    } catch (err) {
      // When responseType is 'blob', error responses come as Blob too
      let message = 'Download failed. Please try again.';
      if (err.response?.data) {
        try {
          // Read the blob as text to get the actual error message
          const text = await err.response.data.text();
          const parsed = JSON.parse(text);
          message = parsed.error || message;
        } catch {
          message = 'Download failed. Please try again.';
        }
      }
      setError(message);
    } finally {
      setDownloading(false);
    }
  };

  const currentFormats = downloadType === 'video'
    ? videoInfo?.video_formats || []
    : videoInfo?.audio_formats || [];

  return (
    <>
      {/* Animated Background */}
      <div className="animated-bg">
        <div className="orb"></div>
        <div className="orb"></div>
        <div className="orb"></div>
      </div>

      <div className="app-container">
        {/* Header */}
        <header className="app-header">
          <div className="logo-icon">
            <DownloadCloudIcon />
          </div>
          <h1>MediaGrab</h1>
          <p>Download videos and audio from YouTube & Instagram in any quality you want</p>
        </header>

        {/* Main Card */}
        <main className="main-card" id="main-downloader-card">
          {/* URL Input */}
          <div className="url-input-group">
            <div className="input-wrapper">
              <div className="input-icon">
                <LinkIcon />
              </div>
              <input
                id="url-input"
                type="url"
                placeholder="Paste YouTube or Instagram URL here..."
                value={url}
                onChange={handleUrlChange}
                onKeyDown={(e) => e.key === 'Enter' && !loading && handleFetchInfo()}
                disabled={loading || downloading}
              />
              {url && (
                <button className="clear-btn" onClick={clearUrl} id="clear-url-btn" aria-label="Clear URL">
                  <XIcon />
                </button>
              )}
            </div>
          </div>

          {/* Platform Badge */}
          {platform && (
            <div className={`platform-badge ${platform}`}>
              {platform === 'youtube' ? <YouTubeIcon /> : <InstagramIcon />}
              {platform === 'youtube' ? 'YouTube' : 'Instagram'} detected
            </div>
          )}

          {/* Download Type Toggle */}
          <div className="type-toggle-wrapper">
            <label>Download As</label>
            <div className="type-toggle">
              <button
                id="toggle-video"
                className={`toggle-option ${downloadType === 'video' ? 'active' : ''}`}
                onClick={() => {
                  setDownloadType('video');
                  setSelectedFormat('best');
                }}
              >
                <VideoIcon />
                Video
              </button>
              <button
                id="toggle-audio"
                className={`toggle-option ${downloadType === 'audio' ? 'active' : ''}`}
                onClick={() => {
                  setDownloadType('audio');
                  setSelectedFormat('best');
                }}
              >
                <AudioIcon />
                Audio
              </button>
            </div>
          </div>

          {/* Quality Selector - shown after fetching info */}
          {videoInfo && currentFormats.length > 0 && (
            <div className="quality-select-wrapper">
              <label>
                {downloadType === 'video' ? 'Video Quality' : 'Audio Quality'}
              </label>
              <select
                id="quality-select"
                className="quality-select"
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value)}
              >
                <option value="best">
                  Best Available Quality
                </option>
                {currentFormats.map((fmt) => (
                  <option key={fmt.format_id} value={fmt.format_id}>
                    {downloadType === 'video'
                      ? `${fmt.resolution} • ${fmt.ext.toUpperCase()}${fmt.fps ? ` • ${fmt.fps}fps` : ''}${fmt.filesize ? ` • ${formatFileSize(fmt.filesize)}` : ''}${fmt.format_note ? ` (${fmt.format_note})` : ''}`
                      : `${fmt.tbr ? `${Math.round(fmt.tbr)}kbps` : 'Unknown bitrate'} • ${fmt.ext.toUpperCase()}${fmt.filesize ? ` • ${formatFileSize(fmt.filesize)}` : ''}`
                    }
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Fetch Info Button */}
          {!videoInfo && !loading && (
            <button
              id="fetch-info-btn"
              className="btn-primary"
              onClick={handleFetchInfo}
              disabled={!url.trim() || !platform}
            >
              <SearchIcon />
              Fetch Media Info
            </button>
          )}

          {/* Loading State */}
          {loading && (
            <div className="loading-overlay">
              <div className="spinner"></div>
              <span className="loading-text">Fetching media information...</span>
            </div>
          )}

          {/* Video Info Preview */}
          {videoInfo && (
            <div className="video-info">
              <div className="video-preview">
                {videoInfo.thumbnail && (
                  <img
                    className="thumbnail"
                    src={videoInfo.thumbnail}
                    alt={videoInfo.title}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
                <div className="video-meta">
                  <h3>{videoInfo.title}</h3>
                  <div className="meta-row">
                    {videoInfo.uploader && <span>{videoInfo.uploader}</span>}
                    {videoInfo.duration > 0 && <span>⏱ {formatDuration(videoInfo.duration)}</span>}
                    {videoInfo.view_count > 0 && <span>👁 {formatViews(videoInfo.view_count)}</span>}
                  </div>
                </div>
              </div>

              {/* Download Button */}
              <button
                id="download-btn"
                className="btn-primary"
                onClick={handleDownload}
                disabled={downloading}
              >
                {downloading ? (
                  <>
                    <div className="spinner" style={{ width: 20, height: 20, borderWidth: 3 }}></div>
                    Downloading...
                  </>
                ) : (
                  <>
                    <DownloadIcon />
                    Download {downloadType === 'video' ? 'Video' : 'Audio'}
                  </>
                )}
              </button>

              {/* Progress Bar */}
              {downloading && (
                <div className="progress-wrapper">
                  <div className="progress-bar-container">
                    <div className="progress-bar-fill" style={{ width: `${progress || 5}%` }}></div>
                  </div>
                  <div className="progress-text">
                    {progress > 0 ? `${progress}% downloaded` : 'Starting download...'}
                  </div>
                </div>
              )}

              {/* New Download Button */}
              <button className="btn-secondary" onClick={clearUrl} id="new-download-btn">
                Start New Download
              </button>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="status-message error" id="error-message">
              <AlertIcon />
              <span>{error}</span>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="status-message success" id="success-message">
              <CheckIcon />
              <span>{success}</span>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="app-footer">
          <div className="supported-platforms">
            <span><YouTubeIcon /> YouTube</span>
            <span><InstagramIcon /> Instagram</span>
          </div>
          <p>MediaGrab — Fast, free, and beautiful media downloader</p>
        </footer>
      </div>
    </>
  );
}

export default App;
