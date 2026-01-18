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
    echo "   Use /upload-cookies endpoint to upload cookies via web interface."
fi

echo "✅ Startup complete!"
echo "🎬 Starting Gunicorn..."

# Start the application
exec gunicorn app:app
