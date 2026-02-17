#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install FFmpeg for yt-dlp audio conversion
apt-get update && apt-get install -y ffmpeg || true

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
