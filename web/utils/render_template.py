from info import BIN_CHANNEL, URL
from utils import temp
import urllib.parse
import html
import logging

# Logger Setup
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 🎨 FAST FINDER STREAMING TEMPLATE
# ─────────────────────────────────────────────
watch_tmplt = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{heading}</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap">
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <style>
        :root {{
            --primary: #009DE0; /* Fast Finder Blue */
            --secondary: #F05A28; /* Fast Finder Orange */
            --bg: #141414;
            --text: #ffffff;
            --nav-bg: rgba(0, 0, 0, 0.7);
        }}
        
        /* Light Mode Colors */
        body.light-mode {{
            --bg: #f4f6f8;
            --text: #1a1a1a;
            --nav-bg: rgba(255, 255, 255, 0.9);
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            font-family: 'Montserrat', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            transition: background 0.3s, color 0.3s;
        }}

        .navbar {{
            padding: 15px 4%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--nav-bg);
            backdrop-filter: blur(10px);
            position: fixed;
            width: 100%;
            z-index: 100;
            top: 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .logo {{
            font-size: 1.8rem;
            font-weight: 800;
            letter-spacing: 1px;
            color: var(--secondary);
            text-transform: uppercase;
        }}
        .logo span {{ color: var(--primary); }}

        .theme-btn {{
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--text);
            transition: transform 0.2s;
        }}
        .theme-btn:hover {{ transform: scale(1.1); }}

        .hero-container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 80px 20px 40px;
            width: 100%;
            max-width: 1000px;
            margin: 0 auto;
        }}

        .player-box {{
            width: 100%;
            border-radius: 12px;
            overflow: hidden;
            background: #000;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            position: relative;
        }}

        .info-section {{ margin-top: 20px; }}

        .title {{
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 15px;
            word-wrap: break-word;
        }}

        .controls-row {{ display: flex; gap: 12px; flex-wrap: wrap; }}

        .btn {{
            display: inline-flex;
            align-items: center;
            padding: 10px 24px;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            border: none;
            transition: opacity 0.2s;
        }}
        .btn:hover {{ opacity: 0.8; }}

        .btn-dl {{ background-color: var(--primary); color: white; }}
        .btn-copy {{ background-color: var(--secondary); color: white; }}

        .plyr--video {{ --plyr-color-main: var(--primary); }}

        #toast {{
            visibility: hidden;
            background-color: #333;
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 99;
            font-weight: 600;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        #toast.show {{ visibility: visible; animation: fade 2.5s; }}

        @keyframes fade {{
            0%, 100% {{ opacity: 0; transform: translateY(10px); }}
            10%, 90% {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body>

    <div class="navbar">
        <div class="logo">FAST<span>FINDER</span></div>
        <button class="theme-btn" onclick="toggleTheme()" title="Toggle Dark/Light Mode">🌓</button>
    </div>

    <div class="hero-container">
        <div class="player-box">
            <video id="player" playsinline>
                <source src="{src}" type="{mime_type}" />
            </video>
        </div>

        <div class="info-section">
            <div class="title">{file_name}</div>
            <div class="controls-row">
                <a href="{src}" class="btn btn-dl">📥 Download</a>
                <button onclick="copyLink()" class="btn btn-copy">📋 Copy Link</button>
            </div>
        </div>
    </div>

    <div id="toast">Link Copied Successfully!</div>

    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script>
        // 1. Theme Toggle Logic
        function toggleTheme() {{
            document.body.classList.toggle('light-mode');
            // Save preference to local storage
            const isLight = document.body.classList.contains('light-mode');
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
        }}

        // Load saved theme
        if(localStorage.getItem('theme') === 'light') {{
            document.body.classList.add('light-mode');
        }}

        // 2. Player Initialization (5s seek enabled natively)
        const player = new Plyr('#player', {{
            controls: ['play-large', 'play', 'progress', 'current-time', 'duration', 'settings', 'pip', 'fullscreen'],
            settings: ['speed'],
            seekTime: 5, // Set native seek time to 5 seconds
            hideControls: true
        }});

        // 3. YouTube-style Double Tap to Seek (5s)
        let lastTap = 0;
        document.querySelector('.player-box').addEventListener('click', function(e) {{
            const currentTime = new Date().getTime();
            const tapLength = currentTime - lastTap;
            
            if (tapLength < 300 && tapLength > 0) {{
                const rect = this.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                
                // If clicked on left half, rewind. Else forward.
                if (clickX < rect.width / 2) {{
                    player.rewind(5);
                }} else {{
                    player.forward(5);
                }}
                e.preventDefault();
            }}
            lastTap = currentTime;
        }});

        // 4. Copy Link Logic
        function copyLink() {{
            navigator.clipboard.writeText("{src}").then(() => {{
                const toast = document.getElementById("toast");
                toast.className = "show";
                setTimeout(() => toast.className = toast.className.replace("show", ""), 2500);
            }}).catch(err => {{
                console.error('Failed to copy: ', err);
            }});
        }}
    </script>
</body>
</html>
"""

async def media_watch(message_id):
    try:
        media_msg = await temp.BOT.get_messages(BIN_CHANNEL, message_id)
        media = getattr(media_msg, media_msg.media.value, None)
        
        if not media:
            return "<h2>❌ File Not Found or Deleted</h2>"

        src = urllib.parse.urljoin(URL, f'download/{message_id}')
        mime_type = getattr(media, 'mime_type', 'video/mp4')
        tag = mime_type.split('/')[0].strip()
        
        if tag == 'video':
            file_name = html.escape(media.file_name if hasattr(media, 'file_name') else "Fast Finder Video")
            
            return watch_tmplt.format(
                heading=f"Watch {file_name}",
                file_name=file_name,
                src=src,
                mime_type=mime_type
            )
        else:
            return f"""
            <body style="background:#141414; color:white; display:flex; align-items:center; justify-content:center; height:100vh; font-family:sans-serif;">
                <div style="text-align:center;">
                    <h1 style="color:#F05A28">⚠️ File Format Not Supported</h1>
                    <p style="margin:10px 0;">Only videos can be streamed directly.</p>
                    <a href="{src}" style="background:#009DE0; color:white; text-decoration:none; font-weight:600; padding:12px 24px; border-radius:6px; margin-top:15px; display:inline-block;">Download File Instead</a>
                </div>
            </body>
            """
    except Exception as e:
        logger.error(f"Template Error: {e}")
        return f"<h2>Server Error: {str(e)}</h2>"
