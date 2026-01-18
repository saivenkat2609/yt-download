#!/usr/bin/env python3
"""
YouTube to R2 Downloader with Anti-Detection
Optimized for Render.com deployment
"""

import os
import sys
import subprocess
import time
import random
import boto3
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# R2 Configuration
R2_ENDPOINT = os.getenv('R2_ENDPOINT')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET = os.getenv('R2_BUCKET_NAME')
R2_COOKIES_FILE = os.getenv('R2_COOKIES_FILE', 'cookies.txt')  # Name of cookies file in R2

# Create downloads directory
DOWNLOAD_DIR = 'downloads'
Path(DOWNLOAD_DIR).mkdir(exist_ok=True)

def download_cookies_from_r2():
    """
    Download cookies.txt from R2 bucket if not present locally
    """
    local_cookies_path = 'cookies.txt'

    # If cookies already exist locally, check if they're fresh (< 7 days old)
    if os.path.exists(local_cookies_path):
        file_age = time.time() - os.path.getmtime(local_cookies_path)
        if file_age < 7 * 24 * 3600:  # Less than 7 days old
            logger.info(f"🍪 Using existing cookies.txt (age: {file_age/86400:.1f} days)")
            return True
        else:
            logger.info(f"🍪 Local cookies are old ({file_age/86400:.1f} days), downloading fresh copy from R2...")

    # Download from R2
    if not all([R2_ENDPOINT, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET]):
        logger.warning("⚠️  R2 credentials not configured, cannot download cookies")
        return False

    try:
        logger.info(f"☁️  Downloading cookies from R2: {R2_BUCKET}/{R2_COOKIES_FILE}")

        s3_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            region_name='auto'
        )

        # Download cookies file
        s3_client.download_file(
            R2_BUCKET,
            R2_COOKIES_FILE,
            local_cookies_path
        )

        # Verify file exists and has content
        if os.path.exists(local_cookies_path) and os.path.getsize(local_cookies_path) > 0:
            logger.info(f"✅ Cookies downloaded successfully from R2 ({os.path.getsize(local_cookies_path)} bytes)")
            return True
        else:
            logger.error("❌ Downloaded cookies file is empty")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to download cookies from R2: {e}")
        logger.warning("⚠️  Continuing without cookies - downloads may fail")
        return False

def random_delay(min_seconds=10, max_seconds=30):
    """
    Random delay to mimic human behavior
    """
    delay = random.uniform(min_seconds, max_seconds)
    logger.info(f"⏳ Waiting {delay:.1f} seconds (anti-detection)...")
    time.sleep(delay)

def check_ytdlp_version():
    """
    Check and update yt-dlp if needed
    """
    try:
        result = subprocess.run(
            ['yt-dlp', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        logger.info(f"ℹ️  yt-dlp version: {version}")
        return True
    except Exception as e:
        logger.error(f"❌ yt-dlp not found or error: {e}")
        return False

def download_youtube_video(url, use_cookies=True, max_retries=3):
    """
    Download YouTube video with anti-detection measures
    Returns the path to the downloaded file
    """
    logger.info(f"📥 Starting download: {url}")

    # Output template with sanitized filename
    output_template = os.path.join(DOWNLOAD_DIR, '%(title).200s.%(ext)s')

    # Build yt-dlp command with anti-detection features
    command = [
        'yt-dlp',
        # Format selection (prefer MP4)
        '--format', 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '--merge-output-format', 'mp4',
        # Output
        '--output', output_template,
        '--no-playlist',
        '--print', 'after_move:filepath',
        # Anti-detection measures
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        '--referer', 'https://www.youtube.com/',
        # Rate limiting
        '--limit-rate', '2M',
        '--sleep-interval', '3',
        '--max-sleep-interval', '7',
        # Network
        '--socket-timeout', '30',
        '--retries', '10',
        '--fragment-retries', '10',
        # Other
        '--no-warnings',
        '--ignore-errors',
    ]

    # Add cookies if file exists
    cookies_path = 'cookies.txt'
    if use_cookies and os.path.exists(cookies_path):
        command.extend(['--cookies', cookies_path])
        logger.info("🍪 Using cookies for authentication")
    else:
        logger.warning("⚠️  No cookies found - download may fail for some videos")

    # Add URL
    command.append(url)

    # Attempt download with retries
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🔄 Attempt {attempt}/{max_retries}")

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=600  # 10 minute timeout
            )

            # Extract file path from output
            output_lines = result.stdout.strip().split('\n')
            filepath = None

            for line in reversed(output_lines):
                if line and os.path.exists(line):
                    filepath = line
                    break

            if filepath and os.path.exists(filepath):
                file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
                logger.info(f"✅ Downloaded successfully: {filepath} ({file_size:.2f} MB)")
                return filepath
            else:
                logger.warning(f"⚠️  Download completed but file not found")

        except subprocess.TimeoutExpired:
            logger.error(f"❌ Attempt {attempt} timed out (10 minutes)")

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Attempt {attempt} failed with exit code {e.returncode}")
            logger.error(f"Error output: {e.stderr[:500]}")

            # Check for specific errors
            if '403' in e.stderr or 'Forbidden' in e.stderr:
                logger.error("🚫 HTTP 403 - Likely rate limited or blocked")
                if attempt < max_retries:
                    wait_time = 60 * attempt  # Progressive backoff
                    logger.info(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
            elif 'Sign in to confirm' in e.stderr:
                logger.error("🤖 Bot detection triggered - Need valid cookies!")
                return None

        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")

        # Wait before retry (except on last attempt)
        if attempt < max_retries:
            random_delay(10, 20)

    logger.error(f"❌ All {max_retries} attempts failed for: {url}")
    return None

def upload_to_r2(file_path, object_name=None):
    """
    Upload file to Cloudflare R2
    """
    if not all([R2_ENDPOINT, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET]):
        logger.error("❌ R2 credentials not configured")
        return False

    if object_name is None:
        object_name = os.path.basename(file_path)

    logger.info(f"☁️  Uploading to R2: {object_name}")

    try:
        # Create S3 client (R2 is S3-compatible)
        s3_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            region_name='auto'
        )

        # Get file size
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB

        # Upload with progress
        def progress_callback(bytes_transferred):
            percent = (bytes_transferred / os.path.getsize(file_path)) * 100
            logger.info(f"📊 Upload progress: {percent:.1f}%")

        # Upload file
        s3_client.upload_file(
            file_path,
            R2_BUCKET,
            object_name,
            ExtraArgs={'ContentType': 'video/mp4'},
            Callback=lambda bytes_transferred: None  # Simplified for now
        )

        logger.info(f"✅ Successfully uploaded to R2: {R2_BUCKET}/{object_name} ({file_size:.2f} MB)")
        return True

    except Exception as e:
        logger.error(f"❌ R2 upload failed: {e}")
        return False

def cleanup_local_file(file_path):
    """
    Delete local file after upload
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑️  Deleted local file: {file_path}")
            return True
    except Exception as e:
        logger.warning(f"⚠️  Could not delete file: {e}")
    return False

def process_video(url, keep_local=False):
    """
    Complete pipeline: download → upload → cleanup
    Returns: (success: bool, message: str)
    """
    start_time = datetime.now()

    logger.info(f"\n{'='*70}")
    logger.info(f"🎬 Processing: {url}")
    logger.info(f"{'='*70}\n")

    try:
        # Step 1: Download video
        file_path = download_youtube_video(url, use_cookies=True)

        if not file_path:
            return False, "Download failed"

        # Step 2: Upload to R2
        upload_success = upload_to_r2(file_path)

        if not upload_success:
            return False, "Upload failed"

        # Step 3: Cleanup (optional)
        if not keep_local:
            cleanup_local_file(file_path)
        else:
            logger.info(f"📁 Keeping local file: {file_path}")

        # Calculate total time
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"\n✨ Successfully processed in {elapsed:.1f} seconds: {url}\n")

        return True, f"Success in {elapsed:.1f}s"

    except Exception as e:
        logger.error(f"❌ Process failed: {e}")
        return False, str(e)

def process_batch(urls, delay_between=True):
    """
    Process multiple videos with delays between each
    """
    results = {
        'success': [],
        'failed': []
    }

    logger.info(f"📋 Starting batch processing: {len(urls)} videos")

    for i, url in enumerate(urls, 1):
        logger.info(f"\n[{i}/{len(urls)}] Processing video...")

        success, message = process_video(url, keep_local=False)

        if success:
            results['success'].append({'url': url, 'message': message})
        else:
            results['failed'].append({'url': url, 'error': message})

        # Random delay between videos (except after last one)
        if delay_between and i < len(urls):
            random_delay(15, 45)  # Longer delays between videos

    # Print summary
    logger.info(f"\n{'='*70}")
    logger.info("📊 BATCH PROCESSING SUMMARY")
    logger.info(f"{'='*70}")
    logger.info(f"✅ Successful: {len(results['success'])}")
    logger.info(f"❌ Failed: {len(results['failed'])}")

    if results['failed']:
        logger.info("\n❌ Failed URLs:")
        for item in results['failed']:
            logger.info(f"  - {item['url']}: {item['error']}")

    return results

def main():
    """
    Main entry point for command-line usage
    """
    if len(sys.argv) < 2:
        print("Usage: python youtube_downloader.py <youtube_url> [--keep-local]")
        print("\nExample:")
        print("  python youtube_downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)

    # Check yt-dlp
    if not check_ytdlp_version():
        logger.error("Please install yt-dlp: pip install yt-dlp")
        sys.exit(1)

    url = sys.argv[1]
    keep_local = '--keep-local' in sys.argv

    # Process video
    success, message = process_video(url, keep_local=keep_local)

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
