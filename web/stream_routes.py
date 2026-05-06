import math
import secrets
import mimetypes
import logging
from urllib.parse import quote
from aiohttp import web
from info import BIN_CHANNEL
from utils import temp
from web.utils.custom_dl import TGCustomYield, chunk_size, offset_fix
from web.utils.render_template import media_watch

routes = web.RouteTableDef()
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 🏠 ROOT ROUTE (FAST FINDER UI — NETFLIX PREMIUM)
# ─────────────────────────────────────────────
@routes.get("/", allow_head=True)
async def root_route_handler(request):
    bot_username = getattr(temp, 'U_NAME', 'AutoFilterBot')

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Fast Finder — Movies, Series & More</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;900&display=swap" rel="stylesheet"/>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ 
        font-family: 'DM Sans', sans-serif; 
        background: #000; 
        color: #fff; 
        min-height: 100vh; 
        display: flex; 
        flex-direction: column; 
    }}
    .hero-bg {{ 
        position: fixed; 
        inset: 0; 
        background: linear-gradient(to top, rgba(0,0,0,1) 0, rgba(0,0,0,0.4) 50%, rgba(0,0,0,0.8) 100%), 
                    url('https://assets.nflxext.com/ffe/siteui/vlv3/f841d4c7-10e1-40af-bcae-07a3f8dc141a/f6d7434e-d6de-4185-a6d4-c77a2d08737b/IN-en-20220502-popsignuptwoweeks-perspective_alpha_website_medium.jpg') center/cover; 
        z-index: -1; 
    }}
    .navbar {{ 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 25px 5%; 
        z-index: 10; 
    }}
    .logo {{ 
        font-size: 28px; 
        font-weight: 900; 
        color: #E50914; 
        text-decoration: none; 
        display: flex; 
        align-items: center; 
        gap: 8px; 
        letter-spacing: 1px; 
        text-transform: uppercase; 
    }}
    .nf-icon {{ 
        background: #E50914; 
        color: #fff; 
        padding: 2px 8px; 
        border-radius: 3px; 
        font-size: 24px; 
        line-height: 1; 
    }}
    .admin-btn {{ 
        background: #E50914; 
        color: #fff; 
        text-decoration: none; 
        padding: 8px 16px; 
        border-radius: 4px; 
        font-weight: 700; 
        font-size: 14px; 
        transition: background 0.2s; 
    }}
    .admin-btn:hover {{ background: #b30710; }}
    
    .hero-content {{ 
        flex: 1; 
        display: flex; 
        flex-direction: column; 
        justify-content: center; 
        align-items: center; 
        text-align: center; 
        padding: 20px; 
        z-index: 10; 
        max-width: 800px; 
        margin: 0 auto; 
    }}
    .hero-title {{ 
        font-size: 4rem; 
        font-weight: 900; 
        margin-bottom: 15px; 
        line-height: 1.1; 
    }}
    .hero-sub {{ 
        font-size: 1.5rem; 
        font-weight: 500; 
        margin-bottom: 30px; 
    }}
    
    .search-container {{ 
        display: flex; 
        width: 100%; 
        max-width: 650px; 
        flex-direction: row; 
    }}
    .search-input {{ 
        flex: 1; 
        padding: 20px 25px; 
        font-size: 1.2rem; 
        border: 1px solid #808080; 
        border-radius: 4px 0 0 4px; 
        background: rgba(0,0,0,0.7); 
        color: #fff; 
        outline: none; 
        transition: 0.2s;
    }}
    .search-input:focus {{ border-color: #fff; }}
    .search-btn {{ 
        background: #E50914; 
        color: #fff; 
        border: none; 
        padding: 0 35px; 
        font-size: 1.5rem; 
        font-weight: 700; 
        border-radius: 0 4px 4px 0; 
        cursor: pointer; 
        display: flex; 
        align-items: center; 
        gap: 10px; 
        transition: 0.2s; 
    }}
    .search-btn:hover {{ background: #b30710; }}
    
    .quick-picks {{ 
        margin-top: 40px; 
        display: flex; 
        flex-wrap: wrap; 
        justify-content: center; 
        gap: 10px; 
    }}
    .qp-title {{ 
        width: 100%; 
        font-size: 1rem; 
        color: #b3b3b3; 
        margin-bottom: 10px; 
        font-weight: 500; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
    }}
    .tag {{ 
        background: rgba(51,51,51,0.8); 
        border: 1px solid #fff; 
        padding: 8px 18px; 
        border-radius: 50px; 
        font-size: 14px; 
        font-weight: 700; 
        cursor: pointer; 
        transition: 0.2s; 
    }}
    .tag:hover {{ background: #fff; color: #000; }}
    
    @media (max-width: 600px) {{
      .hero-title {{ font-size: 2.5rem; }}
      .hero-sub {{ font-size: 1.2rem; }}
      .search-container {{ flex-direction: column; gap: 10px; }}
      .search-input {{ border-radius: 4px; border: 1px solid #808080; padding: 15px; }}
      .search-btn {{ border-radius: 4px; padding: 15px; justify-content: center; font-size: 1.2rem; }}
      .logo {{ font-size: 20px; }}
      .nf-icon {{ font-size: 18px; }}
    }}
  </style>
</head>
<body>
  <div class="hero-bg"></div>
  <header class="navbar">
    <a href="/" class="logo"><span class="nf-icon">F</span> FAST FINDER</a>
    <a href="/admin" class="admin-btn">Admin Panel</a>
  </header>
  
  <main class="hero-content">
    <h1 class="hero-title">Unlimited movies, TV shows, and more.</h1>
    <p class="hero-sub">Search and stream instantly via Telegram.</p>
    
    <div class="search-container">
      <input type="text" id="searchInput" class="search-input" placeholder="Search titles, people, genres..." autocomplete="off">
      <button class="search-btn" onclick="startSearch()">Search ></button>
    </div>
    
    <div class="quick-picks">
      <div class="qp-title">Trending Searches</div>
      <span class="tag" onclick="fillAndSearch('Pushpa 2')">Pushpa 2</span>
      <span class="tag" onclick="fillAndSearch('Jawan')">Jawan</span>
      <span class="tag" onclick="fillAndSearch('Kalki')">Kalki 2898 AD</span>
      <span class="tag" onclick="fillAndSearch('One Piece')">One Piece</span>
      <span class="tag" onclick="fillAndSearch('Animal')">Animal</span>
      <span class="tag" onclick="fillAndSearch('Salaar')">Salaar</span>
    </div>
  </main>

  <script>
    function startSearch() {{
      const q = document.getElementById('searchInput').value.trim();
      const base = `https://t.me/{bot_username}`;
      window.open(q ? `${{base}}?start=${{encodeURIComponent(q)}}` : base, '_blank');
    }}
    function fillAndSearch(q) {{
      document.getElementById('searchInput').value = q;
      startSearch();
    }}
    document.getElementById('searchInput').addEventListener('keydown', e => {{
      if (e.key === 'Enter') startSearch();
    }});
  </script>
</body>
</html>"""
    return web.Response(text=html_content, content_type='text/html')

# ─────────────────────────────────────────────
# 📺 STREAM / WATCH ROUTE
# ─────────────────────────────────────────────
@routes.get("/watch/{message_id}")
async def watch_handler(request):
    try:
        message_id = int(request.match_info['message_id'])
        return web.Response(text=await media_watch(message_id), content_type='text/html')
    except ValueError:
        return web.Response(status=400, text="Invalid Message ID")
    except Exception as e:
        logger.error(f"Watch Error: {e}")
        return web.Response(status=500, text="Internal Server Error")

# ─────────────────────────────────────────────
# 📥 DOWNLOAD ROUTE
# ─────────────────────────────────────────────
@routes.get("/download/{message_id}")
async def download_handler(request):
    try:
        message_id = int(request.match_info['message_id'])
        return await media_download(request, message_id)
    except ValueError:
        return web.Response(status=400, text="Invalid Message ID")
    except Exception as e:
        logger.error(f"Download Error: {e}")
        return web.Response(status=500, text="Internal Server Error")

# ─────────────────────────────────────────────
# 🚀 CORE STREAMING LOGIC (KOYEB OPTIMIZED)
# ─────────────────────────────────────────────
async def media_download(request, message_id: int):
    try:
        media_msg = await temp.BOT.get_messages(BIN_CHANNEL, message_id)
        if not media_msg or not media_msg.media:
            return web.Response(status=404, text="File Not Found or Removed")

        media = getattr(media_msg, media_msg.media.value, None)
        if not media:
            return web.Response(status=404, text="Media Not Supported")

        file_size = media.file_size

        file_name = getattr(media, 'file_name', None)
        if not file_name:
            if getattr(media_msg, 'video', None):
                file_name = f"video_{secrets.token_hex(3)}.mp4"
            elif getattr(media_msg, 'audio', None):
                file_name = f"audio_{secrets.token_hex(3)}.mp3"
            else:
                file_name = f"file_{secrets.token_hex(3)}.bin"

        mime_type = getattr(media, 'mime_type', None)
        if not mime_type:
            mime_guess = mimetypes.guess_type(file_name)[0]
            mime_type = mime_guess if mime_guess else "application/octet-stream"

        range_header = request.headers.get('Range', 0)
        try:
            if range_header:
                from_bytes, until_bytes = range_header.replace('bytes=', '').split('-')
                from_bytes  = int(from_bytes)
                until_bytes = int(until_bytes) if until_bytes else file_size - 1
            else:
                from_bytes  = 0
                until_bytes = file_size - 1
        except Exception:
            from_bytes  = 0
            until_bytes = file_size - 1

        if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
            return web.Response(
                status=416,
                body="416: Range Not Satisfiable",
                headers={"Content-Range": f"bytes */{file_size}"}
            )

        req_length    = until_bytes - from_bytes + 1
        new_chunk_size = await chunk_size(req_length)
        offset        = await offset_fix(from_bytes, new_chunk_size)
        first_part_cut = from_bytes - offset
        last_part_cut  = (until_bytes % new_chunk_size) + 1
        part_count    = math.ceil(req_length / new_chunk_size)

        body = TGCustomYield().yield_file(
            media_msg, offset, first_part_cut, last_part_cut, part_count, new_chunk_size
        )

        encoded_filename = quote(file_name)
        headers = {
            "Content-Type":        mime_type,
            "Content-Range":       f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Disposition": f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}',
            "Accept-Ranges":       "bytes",
            "Content-Length":      str(req_length),
        }

        return web.Response(
            status=206 if range_header else 200,
            body=body,
            headers=headers,
        )

    except Exception as e:
        logger.error(f"Stream Error: {e}")
        return web.Response(status=500, text="Server Error during streaming")
