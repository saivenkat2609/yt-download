#!/bin/bash
# Startup script for Render.com
# Creates cookies.txt from environment variable

echo "🚀 Starting YouTube Downloader..."

# Create cookies.txt from environment variable if it exists
if [ ! -z "$YOUTUBE_COOKIES" ]; then
    echo "🍪 Creating cookies.txt from environment variable..."
    echo "$YOUTUBE_COOKIES" > cookies.txt
    echo "✅ cookies.txt created successfully"
else
    echo "⚠️  WARNING: YOUTUBE_COOKIES environment variable not set!"
    echo "   Downloads may fail without cookies."
fi

# Update yt-dlp to latest version
echo "📦 Updating yt-dlp..."
pip install -U yt-dlp

echo "✅ Startup complete!"
echo "🎬 Starting Gunicorn..."

# Start the application
exec gunicorn app:app
