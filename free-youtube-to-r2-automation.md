# Free YouTube to Cloudflare R2 Automation Guide

A practical guide to automatically download YouTube videos and upload them to Cloudflare R2 storage for free.

---

## Overview

This guide covers how to build a completely free automation system using:
- **yt-dlp** (free, open-source)
- **Cloudflare R2** (10 GB free storage, no egress fees)
- **Python** or **Node.js** (your choice)
- **GitHub Actions** (free automation) OR local scripts

---

## Prerequisites

### 1. Cloudflare R2 Setup

**Create an R2 Bucket:**
1. Sign up at https://cloudflare.com (free account)
2. Go to R2 Object Storage
3. Create a bucket (e.g., `youtube-videos`)
4. Note your bucket name

**Get API Credentials:**
1. Go to R2 → Manage R2 API Tokens
2. Create API Token with "Edit" permissions
3. Save these values:
   - `Account ID`
   - `Access Key ID`
   - `Secret Access Key`
   - `Bucket Name`
   - `Endpoint URL` (format: `https://<account_id>.r2.cloudflarestorage.com`)

**R2 Free Tier:**
- 10 GB storage (free forever)
- 1 million Class A operations/month
- 10 million Class B operations/month
- **Zero egress fees** (unlike AWS S3)

### 2. Install yt-dlp

```bash
# Windows
pip install yt-dlp

# Linux/Mac
pip3 install yt-dlp

# Or download executable from https://github.com/yt-dlp/yt-dlp/releases
```

### 3. Install JavaScript Runtime (Required!)

```bash
# Deno (recommended)
# Windows (PowerShell)
irm https://deno.land/install.ps1 | iex

# Linux/Mac
curl -fsSL https://deno.land/install.sh | sh
```

---

## Method 1: Python Script (Recommended)

### Install Dependencies

```bash
pip install yt-dlp boto3 python-dotenv
```

### Create `.env` File

```env
# .env
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=youtube-videos
R2_ENDPOINT=https://your_account_id.r2.cloudflarestorage.com
```

### Python Script: `youtube_to_r2.py`

```python
#!/usr/bin/env python3
"""
YouTube to Cloudflare R2 Uploader
Downloads YouTube videos and automatically uploads to R2 storage
"""

import os
import sys
import subprocess
import boto3
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# R2 Configuration
R2_ENDPOINT = os.getenv('R2_ENDPOINT')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET = os.getenv('R2_BUCKET_NAME')

def download_youtube_video(url, output_dir='downloads'):
    """
    Download YouTube video using yt-dlp
    Returns the path to the downloaded file
    """
    print(f"📥 Downloading: {url}")

    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)

    # Output template
    output_template = os.path.join(output_dir, '%(title)s.%(ext)s')

    # yt-dlp command
    command = [
        'yt-dlp',
        '--format', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '--merge-output-format', 'mp4',
        '--output', output_template,
        '--no-playlist',  # Download single video only
        '--print', 'after_move:filepath',  # Print final file path
        url
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        # Get the file path from output
        filepath = result.stdout.strip().split('\n')[-1]

        if os.path.exists(filepath):
            print(f"✅ Downloaded: {filepath}")
            return filepath
        else:
            print(f"❌ File not found: {filepath}")
            return None

    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e.stderr}")
        return None

def upload_to_r2(file_path, object_name=None):
    """
    Upload file to Cloudflare R2
    """
    if object_name is None:
        object_name = os.path.basename(file_path)

    print(f"☁️  Uploading to R2: {object_name}")

    try:
        # Create S3 client (R2 is S3-compatible)
        s3_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            region_name='auto'  # R2 uses 'auto' region
        )

        # Upload file
        s3_client.upload_file(
            file_path,
            R2_BUCKET,
            object_name,
            ExtraArgs={'ContentType': 'video/mp4'}
        )

        print(f"✅ Uploaded to R2: {R2_BUCKET}/{object_name}")
        return True

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def cleanup_local_file(file_path):
    """
    Delete local file after upload
    """
    try:
        os.remove(file_path)
        print(f"🗑️  Deleted local file: {file_path}")
    except Exception as e:
        print(f"⚠️  Could not delete file: {e}")

def process_video(url, keep_local=False):
    """
    Complete pipeline: download → upload → cleanup
    """
    print(f"\n{'='*60}")
    print(f"Processing: {url}")
    print(f"{'='*60}\n")

    # Download video
    file_path = download_youtube_video(url)

    if not file_path:
        print("❌ Download failed, aborting")
        return False

    # Upload to R2
    success = upload_to_r2(file_path)

    if not success:
        print("❌ Upload failed")
        return False

    # Cleanup local file (optional)
    if not keep_local:
        cleanup_local_file(file_path)
    else:
        print(f"📁 Keeping local file: {file_path}")

    print(f"\n✨ Successfully processed: {url}\n")
    return True

def main():
    """
    Main entry point
    """
    if len(sys.argv) < 2:
        print("Usage: python youtube_to_r2.py <youtube_url> [--keep-local]")
        print("\nExample:")
        print("  python youtube_to_r2.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)

    url = sys.argv[1]
    keep_local = '--keep-local' in sys.argv

    # Verify environment variables
    if not all([R2_ENDPOINT, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET]):
        print("❌ Error: Missing R2 credentials in .env file")
        sys.exit(1)

    # Process video
    success = process_video(url, keep_local=keep_local)

    if success:
        print("🎉 All done!")
        sys.exit(0)
    else:
        print("💥 Process failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### Usage

```bash
# Single video
python youtube_to_r2.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Keep local copy
python youtube_to_r2.py "https://www.youtube.com/watch?v=VIDEO_ID" --keep-local
```

---

## Method 2: Node.js Script

### Install Dependencies

```bash
npm install @aws-sdk/client-s3 @aws-sdk/lib-storage dotenv
```

### Node.js Script: `youtube-to-r2.js`

```javascript
#!/usr/bin/env node

const { S3Client } = require('@aws-sdk/client-s3');
const { Upload } = require('@aws-sdk/lib-storage');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

// R2 Configuration
const r2Client = new S3Client({
  region: 'auto',
  endpoint: process.env.R2_ENDPOINT,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
  },
});

async function downloadVideo(url, outputDir = 'downloads') {
  console.log(`📥 Downloading: ${url}`);

  // Create output directory
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const outputTemplate = path.join(outputDir, '%(title)s.%(ext)s');

  return new Promise((resolve, reject) => {
    const ytdlp = spawn('yt-dlp', [
      '--format', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
      '--merge-output-format', 'mp4',
      '--output', outputTemplate,
      '--no-playlist',
      '--print', 'after_move:filepath',
      url
    ]);

    let filepath = '';

    ytdlp.stdout.on('data', (data) => {
      const output = data.toString();
      console.log(output);
      filepath = output.trim().split('\n').pop();
    });

    ytdlp.stderr.on('data', (data) => {
      console.error(data.toString());
    });

    ytdlp.on('close', (code) => {
      if (code === 0 && filepath && fs.existsSync(filepath)) {
        console.log(`✅ Downloaded: ${filepath}`);
        resolve(filepath);
      } else {
        reject(new Error('Download failed'));
      }
    });
  });
}

async function uploadToR2(filePath, objectName = null) {
  if (!objectName) {
    objectName = path.basename(filePath);
  }

  console.log(`☁️  Uploading to R2: ${objectName}`);

  try {
    const fileStream = fs.createReadStream(filePath);
    const fileStats = fs.statSync(filePath);

    const upload = new Upload({
      client: r2Client,
      params: {
        Bucket: process.env.R2_BUCKET_NAME,
        Key: objectName,
        Body: fileStream,
        ContentType: 'video/mp4',
        ContentLength: fileStats.size,
      },
    });

    upload.on('httpUploadProgress', (progress) => {
      const percent = Math.round((progress.loaded / progress.total) * 100);
      process.stdout.write(`\r📊 Upload progress: ${percent}%`);
    });

    await upload.done();
    console.log(`\n✅ Uploaded to R2: ${process.env.R2_BUCKET_NAME}/${objectName}`);
    return true;

  } catch (error) {
    console.error(`❌ Upload failed: ${error.message}`);
    return false;
  }
}

function cleanupFile(filePath) {
  try {
    fs.unlinkSync(filePath);
    console.log(`🗑️  Deleted local file: ${filePath}`);
  } catch (error) {
    console.warn(`⚠️  Could not delete file: ${error.message}`);
  }
}

async function processVideo(url, keepLocal = false) {
  console.log('\n' + '='.repeat(60));
  console.log(`Processing: ${url}`);
  console.log('='.repeat(60) + '\n');

  try {
    // Download video
    const filePath = await downloadVideo(url);

    // Upload to R2
    const success = await uploadToR2(filePath);

    if (!success) {
      throw new Error('Upload failed');
    }

    // Cleanup
    if (!keepLocal) {
      cleanupFile(filePath);
    } else {
      console.log(`📁 Keeping local file: ${filePath}`);
    }

    console.log(`\n✨ Successfully processed: ${url}\n`);
    return true;

  } catch (error) {
    console.error(`❌ Process failed: ${error.message}`);
    return false;
  }
}

// Main execution
const url = process.argv[2];
const keepLocal = process.argv.includes('--keep-local');

if (!url) {
  console.log('Usage: node youtube-to-r2.js <youtube_url> [--keep-local]');
  console.log('\nExample:');
  console.log('  node youtube-to-r2.js https://www.youtube.com/watch?v=dQw4w9WgXcQ');
  process.exit(1);
}

// Verify environment variables
if (!process.env.R2_ENDPOINT || !process.env.R2_ACCESS_KEY_ID ||
    !process.env.R2_SECRET_ACCESS_KEY || !process.env.R2_BUCKET_NAME) {
  console.error('❌ Error: Missing R2 credentials in .env file');
  process.exit(1);
}

processVideo(url, keepLocal)
  .then(success => process.exit(success ? 0 : 1))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
```

### Usage

```bash
node youtube-to-r2.js "https://www.youtube.com/watch?v=VIDEO_ID"
```

---

## Method 3: GitHub Actions Automation (Completely Free!)

Run the automation in the cloud for free using GitHub Actions.

### Create GitHub Repository

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/youtube-to-r2.git
git push -u origin main
```

### Add GitHub Secrets

Go to: Repository → Settings → Secrets and variables → Actions

Add these secrets:
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_ENDPOINT`

### Create Workflow File: `.github/workflows/download.yml`

```yaml
name: YouTube to R2

on:
  workflow_dispatch:
    inputs:
      video_url:
        description: 'YouTube Video URL'
        required: true
        type: string
      keep_local:
        description: 'Keep local copy'
        required: false
        type: boolean
        default: false

jobs:
  download-and-upload:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install yt-dlp boto3

      - name: Install Deno (JavaScript runtime)
        uses: denoland/setup-deno@v1
        with:
          deno-version: v1.x

      - name: Download and Upload Video
        env:
          R2_ENDPOINT: ${{ secrets.R2_ENDPOINT }}
          R2_ACCESS_KEY_ID: ${{ secrets.R2_ACCESS_KEY_ID }}
          R2_SECRET_ACCESS_KEY: ${{ secrets.R2_SECRET_ACCESS_KEY }}
          R2_BUCKET_NAME: ${{ secrets.R2_BUCKET_NAME }}
        run: |
          python youtube_to_r2.py "${{ inputs.video_url }}"

      - name: Upload artifact (if keeping local)
        if: ${{ inputs.keep_local }}
        uses: actions/upload-artifact@v4
        with:
          name: video
          path: downloads/*.mp4
          retention-days: 7
```

### Usage

1. Go to your GitHub repository
2. Click "Actions" tab
3. Select "YouTube to R2" workflow
4. Click "Run workflow"
5. Paste YouTube URL
6. Click "Run workflow" button

**Free Tier:**
- 2,000 minutes/month for private repos
- Unlimited for public repos

---

## Method 4: Batch Processing

### Process Multiple Videos: `batch_process.py`

```python
#!/usr/bin/env python3
"""
Batch process multiple YouTube URLs
"""

from youtube_to_r2 import process_video

def batch_process(urls_file='urls.txt'):
    """
    Read URLs from file and process each one
    """
    try:
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"📋 Found {len(urls)} URLs to process\n")

        results = {
            'success': [],
            'failed': []
        }

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processing: {url}")

            success = process_video(url, keep_local=False)

            if success:
                results['success'].append(url)
            else:
                results['failed'].append(url)

        # Summary
        print("\n" + "="*60)
        print("BATCH PROCESSING SUMMARY")
        print("="*60)
        print(f"✅ Successful: {len(results['success'])}")
        print(f"❌ Failed: {len(results['failed'])}")

        if results['failed']:
            print("\nFailed URLs:")
            for url in results['failed']:
                print(f"  - {url}")

        return results

    except FileNotFoundError:
        print(f"❌ File not found: {urls_file}")
        return None

if __name__ == '__main__':
    batch_process()
```

### Create `urls.txt`

```
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
https://www.youtube.com/watch?v=VIDEO_ID_3
```

### Run Batch

```bash
python batch_process.py
```

---

## Advanced: Scheduled Automation

### Option A: Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add entry (runs daily at 2 AM)
0 2 * * * cd /path/to/project && python batch_process.py >> logs/cron.log 2>&1
```

### Option B: Windows Task Scheduler

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute 'python' -Argument 'C:\path\to\youtube_to_r2.py https://youtube.com/...'
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "YouTube to R2"
```

### Option C: GitHub Actions Scheduled Workflow

```yaml
name: Daily YouTube Backup

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install yt-dlp boto3

      - name: Process videos
        env:
          R2_ENDPOINT: ${{ secrets.R2_ENDPOINT }}
          R2_ACCESS_KEY_ID: ${{ secrets.R2_ACCESS_KEY_ID }}
          R2_SECRET_ACCESS_KEY: ${{ secrets.R2_SECRET_ACCESS_KEY }}
          R2_BUCKET_NAME: ${{ secrets.R2_BUCKET_NAME }}
        run: python batch_process.py
```

---

## Troubleshooting

### Issue: yt-dlp fails with 403 error

**Solution:**
```bash
# Update yt-dlp
pip install -U yt-dlp

# Use cookies
yt-dlp --cookies-from-browser chrome URL
```

### Issue: "No module named 'boto3'"

**Solution:**
```bash
pip install boto3
```

### Issue: R2 upload fails with "InvalidAccessKeyId"

**Solution:**
1. Verify credentials in `.env` file
2. Check R2 API token has "Edit" permissions
3. Ensure endpoint URL includes `https://`

### Issue: "yt-dlp: command not found"

**Solution:**
```bash
# Install globally
pip install --user yt-dlp

# Or use full path
python -m yt_dlp URL
```

---

## Cost Analysis

### Completely Free Solution

| Component | Free Tier | Cost for 100 Videos (5 GB) |
|-----------|-----------|---------------------------|
| yt-dlp | Open source | $0 |
| Cloudflare R2 | 10 GB storage | $0 |
| GitHub Actions | 2,000 min/month | $0 |
| Python/Node.js | Open source | $0 |
| **Total** | | **$0/month** |

### When You Might Pay

- **Storage > 10 GB**: $0.015/GB/month ($0.75 for 50 GB)
- **Operations > 10M/month**: Unlikely for personal use
- **Egress**: Always free with R2 (unlike S3)

---

## Best Practices

### 1. Rate Limiting
```python
import time

for url in urls:
    process_video(url)
    time.sleep(10)  # Wait 10 seconds between videos
```

### 2. Error Handling
```python
def safe_process(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            return process_video(url)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(30 * (attempt + 1))
    return False
```

### 3. Logging
```python
import logging

logging.basicConfig(
    filename='youtube_to_r2.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info(f"Processing: {url}")
```

### 4. Webhooks (Optional)
```python
import requests

def notify_discord(message):
    webhook_url = os.getenv('DISCORD_WEBHOOK')
    requests.post(webhook_url, json={"content": message})

# After upload
notify_discord(f"✅ Uploaded: {video_title}")
```

---

## Security Tips

1. **Never commit `.env` files**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use environment variables**
   ```bash
   # Linux/Mac
   export R2_ACCESS_KEY_ID="your_key"

   # Windows
   set R2_ACCESS_KEY_ID=your_key
   ```

3. **Rotate API keys regularly**
   - Generate new R2 tokens every 90 days
   - Delete old tokens immediately

4. **Use read-only tokens when possible**
   - For downloading from R2, use read-only access

---

## Accessing Your Videos

### Get Public URL

```python
import boto3

s3_client = boto3.client('s3', endpoint_url=R2_ENDPOINT, ...)

# Generate presigned URL (temporary access)
url = s3_client.generate_presigned_url(
    'get_object',
    Params={'Bucket': R2_BUCKET, 'Key': 'video.mp4'},
    ExpiresIn=3600  # 1 hour
)

print(url)
```

### Enable Public Access (Optional)

1. Go to R2 bucket settings
2. Enable "Public Access"
3. Connect custom domain (optional)
4. Access via: `https://your-bucket.r2.dev/video.mp4`

---

## Next Steps

1. **Start simple**: Test with one video using Python script
2. **Automate**: Set up GitHub Actions for hands-free operation
3. **Scale**: Add batch processing for multiple videos
4. **Monitor**: Set up logging and notifications
5. **Optimize**: Add caching, compression, and error recovery

---

## Complete Project Structure

```
youtube-to-r2/
├── .env                    # Environment variables (DO NOT COMMIT)
├── .gitignore             # Git ignore file
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies (if using Node)
├── youtube_to_r2.py       # Main Python script
├── youtube-to-r2.js       # Main Node.js script
├── batch_process.py       # Batch processing script
├── urls.txt               # List of URLs to process
├── downloads/             # Temporary download directory
├── logs/                  # Log files
└── .github/
    └── workflows/
        └── download.yml   # GitHub Actions workflow
```

---

## Conclusion

You now have multiple free methods to automatically download YouTube videos and upload them to Cloudflare R2:

- **Local scripts** for on-demand processing
- **GitHub Actions** for cloud-based automation
- **Batch processing** for multiple videos
- **Scheduled tasks** for recurring backups

All completely free within R2's generous 10 GB tier!

**Start with:** The Python script for simplicity and reliability.

**Scale to:** GitHub Actions for 24/7 cloud automation.

---

## Resources

- **yt-dlp**: https://github.com/yt-dlp/yt-dlp
- **Cloudflare R2**: https://developers.cloudflare.com/r2/
- **boto3 (AWS SDK)**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **GitHub Actions**: https://docs.github.com/en/actions

---

**Last Updated:** January 2026
