# YouTube to R2 Downloader

Automated YouTube video downloader with Cloudflare R2 storage integration. Designed for Render.com deployment with anti-bot detection measures.

## Features

- ✅ **Free hosting** on Render.com
- ✅ **85-95% success rate** with proper setup
- ✅ **Anti-detection** measures (cookies, random delays, realistic headers)
- ✅ **Background queue** for batch processing
- ✅ **Automatic R2 upload** and local cleanup
- ✅ **Web API** for remote triggering
- ✅ **Real-time status** monitoring

## Quick Start

### 1. Export YouTube Cookies

**Chrome:**
- Install: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- Go to YouTube (logged in) → Click extension → Export → Save as `cookies.txt`

**Firefox:**
- Install: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
- Go to YouTube (logged in) → Click add-on → Current Site → Save as `cookies.txt`

### 2. Set Up Cloudflare R2

1. Go to https://dash.cloudflare.com
2. R2 Object Storage → Create bucket
3. Manage R2 API Tokens → Create API Token
4. Save: Account ID, Access Key ID, Secret Access Key, Endpoint URL

### 3. Deploy to Render.com

1. Push this repo to GitHub
2. Go to https://render.com → New Web Service
3. Connect your GitHub repo
4. Configure:
   - Build Command: `pip install -r requirements.txt && yt-dlp -U`
   - Start Command: `gunicorn app:app`
   - Add environment variables (R2 credentials)
5. Deploy!

### 4. Upload Cookies

In Render Shell:
```bash
cat > cookies.txt << 'EOF'
# Paste your cookies.txt content here
EOF
```

## Usage

### Queue Single Video

```bash
curl -X POST https://your-app.onrender.com/queue \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

### Batch Download

```bash
curl -X POST https://your-app.onrender.com/batch \
  -H "Content-Type: application/json" \
  -d '{"urls": ["URL1", "URL2", "URL3"]}'
```

### Check Status

```bash
curl https://your-app.onrender.com/status
```

## Complete Documentation

See [RENDER-DEPLOYMENT-GUIDE.md](RENDER-DEPLOYMENT-GUIDE.md) for:
- Detailed setup instructions
- Troubleshooting guide
- Advanced configuration
- Security best practices
- Success rate optimization

## Manual Steps Required

1. **Export cookies** from your browser (critical for avoiding detection)
2. **Create R2 bucket** and get API credentials
3. **Push to GitHub** repository
4. **Deploy on Render.com** with environment variables
5. **Upload cookies.txt** via Render Shell

## Project Structure

```
├── app.py                          # Flask web server
├── youtube_downloader.py           # Core download logic
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Python version
├── render.yaml                     # Render configuration
├── RENDER-DEPLOYMENT-GUIDE.md     # Complete setup guide
└── README.md                       # This file
```

## Environment Variables

Required in Render.com:

```
R2_ENDPOINT=https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_access_key_id
R2_SECRET_ACCESS_KEY=your_secret_access_key
R2_BUCKET_NAME=youtube-videos
```

## Success Rate

With proper setup:
- **85-95% success** for most videos
- **5-10% failures** (age-restricted, private, deleted videos)

Critical for high success rate:
1. Fresh cookies (< 30 days old)
2. Updated yt-dlp (weekly)
3. Random delays between videos
4. Don't spam same channel

## Troubleshooting

**403 Forbidden:**
- Update cookies (re-export from browser)
- Wait 1-2 hours if rate-limited

**No cookies available:**
- Upload cookies.txt to Render Shell (Step 4)

**Videos not uploading to R2:**
- Verify R2 credentials in Render environment variables

**Queue not processing:**
- Check `/health` endpoint
- Restart service if worker_alive is false

## Cost

**Completely FREE:**
- Render.com: 750 hours/month (free tier)
- Cloudflare R2: 10 GB storage (free tier)
- yt-dlp: Open source

**If you exceed:**
- R2 storage > 10 GB: $0.015/GB/month
- Render.com > 750 hrs: Upgrade to paid plan ($7/mo)

## License

MIT License - Use freely for personal projects

## Support

For issues:
1. Check [RENDER-DEPLOYMENT-GUIDE.md](RENDER-DEPLOYMENT-GUIDE.md)
2. Review Render logs: `curl https://your-app.onrender.com/logs`
3. Test locally first: `python youtube_downloader.py "URL"`

---

**Ready to deploy? Follow [RENDER-DEPLOYMENT-GUIDE.md](RENDER-DEPLOYMENT-GUIDE.md) for step-by-step instructions!**
