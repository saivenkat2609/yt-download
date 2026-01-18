#!/usr/bin/env python3
"""
Simple script to submit videos to your Render.com YouTube downloader
"""

import requests
import time
import sys

# CHANGE THIS to your Render.com app URL
RENDER_URL = "https://your-app-name.onrender.com"

def check_health():
    """Check if service is healthy"""
    try:
        response = requests.get(f"{RENDER_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Service Health Check:")
            print(f"   - yt-dlp installed: {data.get('ytdlp_installed')}")
            print(f"   - R2 configured: {data.get('r2_configured')}")
            print(f"   - Cookies available: {data.get('cookies_available')}")
            print(f"   - Worker alive: {data.get('worker_alive')}")
            return data.get('cookies_available') and data.get('r2_configured')
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
        return False

def submit_single(url):
    """Submit single video to queue"""
    try:
        response = requests.post(
            f"{RENDER_URL}/queue",
            json={"url": url},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Queued: {url}")
            print(f"   Queue position: {data.get('queue_position', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed: {url}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error submitting {url}: {e}")
        return False

def submit_batch(urls):
    """Submit multiple videos at once"""
    try:
        response = requests.post(
            f"{RENDER_URL}/batch",
            json={"urls": urls},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Batch queued: {len(urls)} videos")
            print(f"   Queue size: {data.get('queue_size', 'Unknown')}")
            return True
        else:
            print(f"❌ Batch failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error submitting batch: {e}")
        return False

def check_status():
    """Check processing status"""
    try:
        response = requests.get(f"{RENDER_URL}/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("\n📊 Current Status:")
            print(f"   Currently processing: {data.get('currently_processing', 'None')}")
            print(f"   Queue size: {data.get('queue_size', 0)}")
            print(f"   Total completed: {data.get('total_completed', 0)}")
            print(f"   Total failed: {data.get('total_failed', 0)}")
            return data
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Cannot get status: {e}")
        return None

def main():
    print("=" * 70)
    print("YouTube to R2 Downloader - Video Submission Tool")
    print("=" * 70)
    print()

    # Check if RENDER_URL is configured
    if "your-app-name" in RENDER_URL:
        print("⚠️  WARNING: Please update RENDER_URL in this script!")
        print("   Change 'your-app-name' to your actual Render.com app name")
        print()
        return

    # Health check
    print("Checking service health...")
    if not check_health():
        print("\n❌ Service is not ready. Please check:")
        print("   1. Render.com service is running")
        print("   2. R2 credentials are configured")
        print("   3. cookies.txt is uploaded")
        return

    print()

    # Example usage
    if len(sys.argv) > 1:
        # URLs provided as command line arguments
        urls = sys.argv[1:]

        if len(urls) == 1:
            # Single video
            submit_single(urls[0])
        else:
            # Multiple videos
            print(f"Submitting {len(urls)} videos...")
            submit_batch(urls)
    else:
        # Interactive mode
        print("Usage Options:")
        print()
        print("1. Submit single video:")
        print("   python submit_videos.py 'https://youtube.com/watch?v=VIDEO_ID'")
        print()
        print("2. Submit multiple videos:")
        print("   python submit_videos.py 'URL1' 'URL2' 'URL3'")
        print()
        print("3. Interactive mode (enter URLs one by one):")
        print()

        urls = []
        print("Enter YouTube URLs (one per line, blank line to finish):")
        while True:
            url = input("> ").strip()
            if not url:
                break
            urls.append(url)

        if urls:
            if len(urls) == 1:
                submit_single(urls[0])
            else:
                print(f"\nSubmitting {len(urls)} videos with delays...")
                # Submit one by one with small delay
                for i, url in enumerate(urls, 1):
                    print(f"\n[{i}/{len(urls)}]")
                    submit_single(url)
                    if i < len(urls):
                        time.sleep(2)  # Small delay between submissions
        else:
            print("No URLs provided.")

    # Show final status
    print()
    check_status()

    print()
    print("=" * 70)
    print("✨ Done! Videos are processing in the background.")
    print("   Check status anytime: python submit_videos.py --status")
    print("=" * 70)

if __name__ == '__main__':
    if '--status' in sys.argv:
        check_status()
    else:
        main()
