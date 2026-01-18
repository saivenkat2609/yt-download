# Manual Steps Required - Quick Checklist

## Before Deployment

### ☑️ Step 1: Export YouTube Cookies (5 minutes)

**Why:** Critical for avoiding bot detection (85%+ success rate depends on this)

**How:**

**Chrome:**
1. Install extension: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
2. Go to https://youtube.com and LOG IN
3. Click extension icon → "Export" → Save as `cookies.txt`

**Firefox:**
1. Install: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/
2. Go to https://youtube.com and LOG IN
3. Click add-on → "Current Site" → Save as `cookies.txt`

**Save this file - you'll need it in Step 5!**

---

### ☑️ Step 2: Create Cloudflare R2 Account (5 minutes)

**Why:** Free 10 GB storage for your videos (no egress fees)

**How:**

1. Go to https://dash.cloudflare.com
2. Sign up (free account)
3. Navigate to **R2 Object Storage**
4. Click **"Create bucket"**
5. Name: `youtube-videos` (or anything)
6. Click **"Create bucket"**

**✅ Bucket created!**

---

### ☑️ Step 3: Get R2 API Credentials (3 minutes)

**Why:** Your app needs these to upload videos to R2

**How:**

1. In Cloudflare: **R2 → Manage R2 API Tokens**
2. Click **"Create API Token"**
3. Name: `youtube-downloader`
4. Permissions: **"Object Read & Write"**
5. Click **"Create API Token"**

**📝 COPY THESE (you can't view secret key again!):**

```
Account ID: _____________________________
Access Key ID: _____________________________
Secret Access Key: _____________________________
Endpoint URL: https://______________.r2.cloudflarestorage.com
```

**Save these somewhere safe - you'll paste them in Step 6!**

---

### ☑️ Step 4: Push Code to GitHub (2 minutes)

**Why:** Render.com deploys from GitHub

**How:**

```bash
# In your project directory
git init
git add .
git commit -m "Initial commit"

# Create new repo on GitHub.com, then:
git remote add origin https://github.com/YOUR_USERNAME/youtube-to-r2.git
git push -u origin main
```

**✅ Code is on GitHub!**

---

## During Deployment

### ☑️ Step 5: Deploy on Render.com (5 minutes)

**Why:** Free hosting (750 hours/month)

**How:**

1. Go to https://render.com
2. Sign up with GitHub
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repo
5. Configure:
   - Name: `youtube-downloader`
   - Build: `pip install -r requirements.txt && yt-dlp -U`
   - Start: `gunicorn app:app`
   - Instance: **Free**
6. Click **"Create Web Service"**

**⏳ Wait 3-5 minutes for deployment...**

---

### ☑️ Step 6: Add Environment Variables in Render (2 minutes)

**Why:** Your app needs R2 credentials to work

**How:**

1. In Render dashboard → Your service
2. Go to **"Environment"** tab
3. Click **"Add Environment Variable"**
4. Add these 4 (use your credentials from Step 3):

```
R2_ENDPOINT = https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID = your_access_key_from_step_3
R2_SECRET_ACCESS_KEY = your_secret_key_from_step_3
R2_BUCKET_NAME = youtube-videos
```

5. Click **"Save Changes"**

**✅ Service will restart automatically**

---

## After Deployment

### ☑️ Step 7: Upload Cookies to Render (3 minutes)

**Why:** Without cookies, you'll get bot detection / 403 errors

**How:**

1. In Render dashboard → Your service
2. Click **"Shell"** tab (top right)
3. Terminal opens - type this:

```bash
cat > cookies.txt << 'EOF'
```

4. Open your `cookies.txt` (from Step 1) on your computer
5. Copy ALL content
6. Paste into Render Shell
7. Press Enter
8. Type `EOF` and press Enter

**Verify it worked:**
```bash
ls -lh cookies.txt
```

Should show file size > 0 bytes.

**✅ Cookies uploaded!**

---

### ☑️ Step 8: Test Your Setup (2 minutes)

**Why:** Make sure everything works before processing 10-20 videos

**How:**

```bash
# Check health (replace YOUR-APP with your Render app name)
curl https://YOUR-APP.onrender.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "ytdlp_installed": true,
  "r2_configured": true,
  "cookies_available": true,
  "worker_alive": true
}
```

**If all are `true` - YOU'RE READY! ✅**

**Test with one video:**
```bash
curl -X POST https://YOUR-APP.onrender.com/queue \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

**Check status:**
```bash
curl https://YOUR-APP.onrender.com/status
```

---

## Daily Usage

### Download 10-20 Videos

**Option 1: One by one**
```bash
curl -X POST https://YOUR-APP.onrender.com/queue \
  -H "Content-Type: application/json" \
  -d '{"url": "YOUTUBE_URL"}'
```

**Option 2: Batch (all at once)**
```bash
curl -X POST https://YOUR-APP.onrender.com/batch \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://youtube.com/watch?v=VIDEO_1",
      "https://youtube.com/watch?v=VIDEO_2",
      "... up to 20 ..."
    ]
  }'
```

Videos process in background with automatic delays to avoid detection.

---

## Maintenance (Monthly)

### ☑️ Update Cookies (Monthly)

Cookies expire after ~30 days.

1. Re-export cookies from browser (Step 1)
2. Upload to Render Shell (Step 7)

### ☑️ Update yt-dlp (Weekly)

YouTube changes frequently.

**Option 1: Trigger re-deploy**
```bash
git commit --allow-empty -m "Update yt-dlp"
git push origin main
```

**Option 2: Manual update in Shell**
```bash
pip install -U yt-dlp
```

---

## Troubleshooting

**Problem: `cookies_available: false`**
- Solution: Complete Step 7 (upload cookies)

**Problem: 403 Forbidden errors**
- Solution: Update cookies (Step 1 + Step 7)

**Problem: Videos not uploading to R2**
- Solution: Check R2 credentials in Step 6

**Problem: Queue not processing**
- Solution: Check `/health`, restart service if needed

---

## Summary

**Manual steps required:**
1. ✅ Export cookies (5 min) - ONE TIME
2. ✅ Create R2 account + bucket (5 min) - ONE TIME
3. ✅ Get R2 credentials (3 min) - ONE TIME
4. ✅ Push to GitHub (2 min) - ONE TIME
5. ✅ Deploy on Render (5 min) - ONE TIME
6. ✅ Add R2 credentials to Render (2 min) - ONE TIME
7. ✅ Upload cookies to Render (3 min) - ONE TIME, then monthly
8. ✅ Test setup (2 min) - ONE TIME

**Total setup time: ~25 minutes**

**After setup:**
- Download 10-20 videos daily via API
- Update cookies monthly
- Update yt-dlp weekly
- Everything else is automatic!

---

**Complete guide:** See `RENDER-DEPLOYMENT-GUIDE.md` for detailed instructions.

**Quick reference:** See `README.md` for API usage examples.
