#!/usr/bin/env python3
"""
Flask Web Server for YouTube Downloader
Runs on Render.com and provides API endpoints
"""

from flask import Flask, request, jsonify
import threading
import queue
import logging
from youtube_downloader import process_video, process_batch, check_ytdlp_version
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Queue for background processing
video_queue = queue.Queue()
processing_status = {
    'current': None,
    'queue_size': 0,
    'completed': 0,
    'failed': 0
}

def background_worker():
    """
    Background thread that processes videos from queue
    """
    logger.info("🚀 Background worker started")

    while True:
        try:
            # Get video from queue (blocking)
            video_data = video_queue.get()

            if video_data is None:  # Poison pill to stop worker
                break

            url = video_data['url']
            processing_status['current'] = url
            processing_status['queue_size'] = video_queue.qsize()

            logger.info(f"📥 Processing from queue: {url}")

            # Process video
            success, message = process_video(url, keep_local=False)

            if success:
                processing_status['completed'] += 1
                logger.info(f"✅ Queue processing success: {url}")
            else:
                processing_status['failed'] += 1
                logger.error(f"❌ Queue processing failed: {url} - {message}")

            processing_status['current'] = None
            processing_status['queue_size'] = video_queue.qsize()

            video_queue.task_done()

        except Exception as e:
            logger.error(f"❌ Worker error: {e}")

# Start background worker thread
worker_thread = threading.Thread(target=background_worker, daemon=True)
worker_thread.start()

@app.route('/')
def home():
    """
    Home page with API documentation
    """
    return """
    <html>
    <head>
        <title>YouTube to R2 Downloader</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
            pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
            .endpoint { margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; background: #f8f9fa; }
        </style>
    </head>
    <body>
        <h1>🎬 YouTube to R2 Downloader API</h1>
        <p>Server is running! Use the API endpoints below to download videos.</p>

        <div class="endpoint">
            <h3>GET /health</h3>
            <p>Check server health and status</p>
            <pre>curl https://your-app.onrender.com/health</pre>
        </div>

        <div class="endpoint">
            <h3>POST /download</h3>
            <p>Download a single video (immediate processing)</p>
            <pre>curl -X POST https://your-app.onrender.com/download \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'</pre>
        </div>

        <div class="endpoint">
            <h3>POST /queue</h3>
            <p>Add video to background queue (recommended for multiple videos)</p>
            <pre>curl -X POST https://your-app.onrender.com/queue \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'</pre>
        </div>

        <div class="endpoint">
            <h3>POST /batch</h3>
            <p>Add multiple videos to queue at once</p>
            <pre>curl -X POST https://your-app.onrender.com/batch \\
  -H "Content-Type: application/json" \\
  -d '{"urls": ["https://youtube.com/watch?v=ID1", "https://youtube.com/watch?v=ID2"]}'</pre>
        </div>

        <div class="endpoint">
            <h3>GET /status</h3>
            <p>Check processing status and queue</p>
            <pre>curl https://your-app.onrender.com/status</pre>
        </div>

        <div class="endpoint">
            <h3>GET/POST /upload-cookies</h3>
            <p><strong>⭐ NEW: Upload cookies via web form (no Shell access needed!)</strong></p>
            <p>Visit this page in your browser to paste and upload cookies.txt</p>
            <pre>https://your-app.onrender.com/upload-cookies</pre>
        </div>

        <p><strong>⚠️ Important:</strong> Upload your YouTube cookies first at <a href="/upload-cookies">/upload-cookies</a> before downloading videos!</p>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """
    Health check endpoint
    """
    ytdlp_ok = check_ytdlp_version()
    r2_configured = all([
        os.getenv('R2_ENDPOINT'),
        os.getenv('R2_ACCESS_KEY_ID'),
        os.getenv('R2_SECRET_ACCESS_KEY'),
        os.getenv('R2_BUCKET_NAME')
    ])
    cookies_exist = os.path.exists('cookies.txt')

    return jsonify({
        'status': 'healthy',
        'ytdlp_installed': ytdlp_ok,
        'r2_configured': r2_configured,
        'cookies_available': cookies_exist,
        'worker_alive': worker_thread.is_alive(),
        'queue_size': video_queue.qsize(),
        'stats': processing_status
    })

@app.route('/download', methods=['POST'])
def download():
    """
    Download video immediately (synchronous)
    Use for single videos, but may timeout on Render
    """
    try:
        data = request.get_json()

        if not data or 'url' not in data:
            return jsonify({'error': 'Missing "url" in request body'}), 400

        url = data['url']

        logger.info(f"📥 Received immediate download request: {url}")

        # Process video immediately
        success, message = process_video(url, keep_local=False)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'url': url
            })
        else:
            return jsonify({
                'success': False,
                'error': message,
                'url': url
            }), 500

    except Exception as e:
        logger.error(f"❌ Download endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/queue', methods=['POST'])
def add_to_queue():
    """
    Add video to background processing queue (recommended)
    Returns immediately, video processes in background
    """
    try:
        data = request.get_json()

        if not data or 'url' not in data:
            return jsonify({'error': 'Missing "url" in request body'}), 400

        url = data['url']

        logger.info(f"📋 Adding to queue: {url}")

        # Add to queue
        video_queue.put({'url': url})

        return jsonify({
            'success': True,
            'message': 'Video added to queue',
            'url': url,
            'queue_position': video_queue.qsize(),
            'currently_processing': processing_status['current']
        })

    except Exception as e:
        logger.error(f"❌ Queue endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/batch', methods=['POST'])
def batch_queue():
    """
    Add multiple videos to queue at once
    """
    try:
        data = request.get_json()

        if not data or 'urls' not in data:
            return jsonify({'error': 'Missing "urls" array in request body'}), 400

        urls = data['urls']

        if not isinstance(urls, list):
            return jsonify({'error': '"urls" must be an array'}), 400

        logger.info(f"📋 Adding {len(urls)} videos to queue")

        # Add all to queue
        for url in urls:
            video_queue.put({'url': url})

        return jsonify({
            'success': True,
            'message': f'Added {len(urls)} videos to queue',
            'urls_count': len(urls),
            'queue_size': video_queue.qsize(),
            'currently_processing': processing_status['current']
        })

    except Exception as e:
        logger.error(f"❌ Batch endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    """
    Get current processing status
    """
    return jsonify({
        'currently_processing': processing_status['current'],
        'queue_size': video_queue.qsize(),
        'total_completed': processing_status['completed'],
        'total_failed': processing_status['failed'],
        'worker_alive': worker_thread.is_alive()
    })

@app.route('/logs')
def logs():
    """
    View recent logs (last 50 lines)
    """
    try:
        if os.path.exists('youtube_downloader.log'):
            with open('youtube_downloader.log', 'r') as f:
                lines = f.readlines()
                recent_logs = lines[-50:]  # Last 50 lines
                return '<pre>' + ''.join(recent_logs) + '</pre>'
        else:
            return '<pre>No logs available</pre>'
    except Exception as e:
        return f'<pre>Error reading logs: {e}</pre>'

@app.route('/upload-cookies', methods=['GET', 'POST'])
def upload_cookies():
    """
    Upload cookies.txt via web interface (workaround for no Shell access)
    """
    if request.method == 'GET':
        # Show upload form
        return """
        <html>
        <head>
            <title>Upload Cookies</title>
            <style>
                body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
                textarea { width: 100%; height: 300px; font-family: monospace; font-size: 12px; }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
                button:hover { background: #0056b3; }
                .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>🍪 Upload YouTube Cookies</h1>
            <p>Paste the <strong>entire content</strong> of your cookies.txt file below:</p>
            <form method="POST">
                <textarea name="cookies" placeholder="# Netscape HTTP Cookie File
# This is a generated file! Do not edit.
.youtube.com	TRUE	/	TRUE	1735689600	VISITOR_INFO1_LIVE	...
..."></textarea>
                <br><br>
                <button type="submit">Upload Cookies</button>
            </form>
            <br>
            <p><strong>Instructions:</strong></p>
            <ol>
                <li>Export cookies from your browser (Chrome/Firefox extension)</li>
                <li>Open cookies.txt in Notepad</li>
                <li>Copy ALL content (Ctrl+A, Ctrl+C)</li>
                <li>Paste above and click Upload</li>
            </ol>
            <p><a href="/health">← Back to Health Check</a></p>
        </body>
        </html>
        """
    else:
        # Handle upload
        try:
            cookies_content = request.form.get('cookies', '').strip()

            if not cookies_content:
                return """
                <html><body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
                    <div class="error">❌ Error: No cookies content provided!</div>
                    <a href="/upload-cookies">← Try Again</a>
                </body></html>
                """

            # Write to cookies.txt
            with open('cookies.txt', 'w') as f:
                f.write(cookies_content)

            logger.info(f"✅ Cookies uploaded successfully via web interface ({len(cookies_content)} bytes)")

            return """
            <html>
            <head>
                <title>Upload Success</title>
                <style>
                    body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
                    .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <h1>✅ Cookies Uploaded Successfully!</h1>
                <div class="success">
                    <p><strong>Cookies file created:</strong> cookies.txt</p>
                    <p><strong>Size:</strong> """ + str(len(cookies_content)) + """ bytes</p>
                </div>
                <p>Your cookies are now active. You can start downloading videos!</p>
                <p><a href="/health">Check Health Status</a> | <a href="/">Home</a></p>
            </body>
            </html>
            """

        except Exception as e:
            logger.error(f"❌ Cookie upload failed: {e}")
            return f"""
            <html><body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
                <div class="error">❌ Error: {e}</div>
                <a href="/upload-cookies">← Try Again</a>
            </body></html>
            """

if __name__ == '__main__':
    # Get port from environment (Render provides PORT env var)
    port = int(os.getenv('PORT', 10000))

    logger.info(f"🚀 Starting YouTube Downloader API on port {port}")
    logger.info(f"🔗 Access at http://0.0.0.0:{port}")

    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
