from aiohttp import web
import time
import uuid
from info import ADMIN_USERNAME, ADMIN_PASSWORD, ADMINS
from utils import temp
from database.users_chats_db import db as user_db
from database.ia_filterdb import db_count_documents, COLLECTIONS
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_routes = web.RouteTableDef()

def is_logged_in(request):
    session_id = request.cookies.get('admin_session')
    if not hasattr(temp, 'ADMIN_SESSIONS'): return False
    return session_id in temp.ADMIN_SESSIONS and time.time() < temp.ADMIN_SESSIONS[session_id]

THEME_SCRIPT = """
<script>
    const savedTheme = localStorage.getItem('adminTheme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('adminTheme', newTheme);
        document.getElementById('theme-icon').className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
</script>
"""

@admin_routes.get('/admin')
async def login_page(request):
    html = f"""
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <style>
        :root {{ --bg: #0d1117; --box-bg: #161b22; --text: #c9d1d9; --input-bg: #010409; --border: #30363d; --primary: #00d2ff; --btn-text: #0d1117; }}
        [data-theme="light"] {{ --bg: #f6f8fa; --box-bg: #ffffff; --text: #24292f; --input-bg: #f6f8fa; --border: #d0d7de; --primary: #0969da; --btn-text: #ffffff; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: var(--bg); margin: 0; color: var(--text); transition: background 0.3s; }}
        .box {{ background: var(--box-bg); padding: 40px 30px; border-radius: 12px; border: 1px solid var(--border); box-shadow: 0 8px 24px rgba(0,0,0,0.1); width: 100%; max-width: 320px; text-align: center; position: relative; }}
        .theme-btn {{ position: absolute; top: 15px; right: 15px; background: none; border: none; color: var(--text); font-size: 20px; cursor: pointer; outline: none; }}
        h2 {{ margin-top: 0; margin-bottom: 25px; font-weight: 600; color: var(--primary); }}
        input {{ width: 100%; padding: 12px 15px; margin: 10px 0; border: 1px solid var(--border); border-radius: 6px; background: var(--input-bg); color: var(--text); box-sizing: border-box; outline: none; font-size: 14px; transition: 0.2s; }}
        input:focus {{ border-color: var(--primary); outline: none; box-shadow: 0 0 0 3px rgba(0, 210, 255, 0.3); }}
        button[type="submit"] {{ width: 100%; padding: 12px; background: var(--primary); color: var(--btn-text); border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 15px; margin-top: 15px; transition: 0.2s; }}
        button[type="submit"]:hover {{ filter: brightness(1.1); }}
    </style>
    {THEME_SCRIPT}
    </head><body>
    <div class="box">
        <button class="theme-btn" onclick="toggleTheme()"><i id="theme-icon" class="fas fa-sun"></i></button>
        <h2><i class="fas fa-shield-alt"></i> Admin Login</h2>
        <form action="/login" method="post">
            <input type="text" name="user" placeholder="Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button type="submit">Log in</button>
        </form>
    </div>
    <script>document.getElementById('theme-icon').className = document.documentElement.getAttribute('data-theme') === 'dark' ? 'fas fa-sun' : 'fas fa-moon';</script>
    </body></html>
    """
    return web.Response(text=html, content_type='text/html')

@admin_routes.post('/login')
async def login_post(request):
    data = await request.post()
    if data.get('user') == ADMIN_USERNAME and data.get('pass') == ADMIN_PASSWORD:
        session_id = str(uuid.uuid4())
        if not hasattr(temp, 'ADMIN_SESSIONS'): temp.ADMIN_SESSIONS = {}
        temp.ADMIN_SESSIONS[session_id] = time.time() + 3600
        res = web.HTTPFound('/dashboard')
        res.set_cookie('admin_session', session_id, max_age=3600)
        try:
            btn = [[InlineKeyboardButton("🛑 Disconnect Session", callback_data=f"logout_{session_id}")]]
            await temp.BOT.send_message(chat_id=ADMINS[0], text="✅ **Web Login Detected!**\nYour session is active.", reply_markup=InlineKeyboardMarkup(btn))
        except: pass
        return res
    return web.Response(text="<html><body style='background:#0d1117;color:#f85149;text-align:center;padding:50px;font-family:sans-serif;'><h2>❌ Access Denied!</h2><a href='/admin' style='color:#58a6ff;text-decoration:none;'>Go Back</a></body></html>", content_type='text/html')

@admin_routes.get('/dashboard')
async def admin_dashboard(request):
    if not is_logged_in(request): return web.HTTPFound('/admin')
    stats = await db_count_documents()
    total_u = await user_db.total_users_count()

    html = f"""
    <!DOCTYPE html><html lang="en"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Control Center</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <style>
        :root {{ --bg: #0d1117; --card-bg: #161b22; --text: #c9d1d9; --text-muted: #8b949e; --border: #30363d; --primary: #00d2ff; --primary-bg: rgba(0,210,255,0.1); --cloud: #2ea043; --cloud-bg: rgba(46,160,67,0.1); --archive: #d29922; --archive-bg: rgba(210,153,34,0.1); --hover: #1f242c; --btn-text: #0d1117; }}
        [data-theme="light"] {{ --bg: #f6f8fa; --card-bg: #ffffff; --text: #24292f; --text-muted: #57606a; --border: #d0d7de; --primary: #0969da; --primary-bg: #ddf4ff; --cloud: #1a7f37; --cloud-bg: #dafbe1; --archive: #9a6700; --archive-bg: #fff8c5; --hover: #f3f4f6; --btn-text: #ffffff; }}
        
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; transition: all 0.2s; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        
        /* Stats Grid */
        .dashboard-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 25px; }}
        .dashboard-box {{ background-color: var(--card-bg); border-radius: 12px; padding: 20px; display: flex; align-items: center; border: 1px solid var(--border); }}
        .icon-box {{ padding: 15px; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 15px; width: 25px; height: 25px; font-size: 22px; }}
        .text-box h3 {{ margin: 0; font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }}
        .text-box p {{ margin: 5px 0 0; font-size: 24px; font-weight: bold; color: var(--text); }}
        
        /* Colors for Stats */
        .db-total {{ border-left: 4px solid var(--text-muted); }} .db-total .icon-box {{ background-color: rgba(139,148,158,0.1); color: var(--text-muted); }}
        .db-primary {{ border-left: 4px solid var(--primary); }} .db-primary .icon-box {{ background-color: var(--primary-bg); color: var(--primary); }}
        .db-cloud {{ border-left: 4px solid var(--cloud); }} .db-cloud .icon-box {{ background-color: var(--cloud-bg); color: var(--cloud); }}
        .db-archive {{ border-left: 4px solid var(--archive); }} .db-archive .icon-box {{ background-color: var(--archive-bg); color: var(--archive); }}

        /* Search Section */
        .search-area {{ background-color: var(--card-bg); border-radius: 12px; padding: 20px; border: 1px solid var(--border); }}
        .search-form {{ display: flex; gap: 10px; flex-wrap: wrap; }}
        .search-form select, .search-form input {{ background: var(--bg); color: var(--text); padding: 12px 15px; border-radius: 8px; border: 1px solid var(--border); outline: none; font-size: 14px; }}
        .search-form input {{ flex-grow: 1; min-width: 200px; }}
        .search-form input:focus {{ border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-bg); }}
        .btn-search {{ background: var(--primary); color: var(--btn-text); padding: 12px 20px; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; transition: 0.2s; display: flex; align-items: center; gap: 8px; }}
        .btn-search:hover {{ filter: brightness(1.1); }}
        
        /* Table Design */
        .results-header {{ display: none; align-items: center; color: var(--primary); font-weight: bold; font-size: 15px; margin: 20px 0 10px; }}
        .table-container {{ overflow-x: auto; }}
        .results-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        .results-table th, .results-table td {{ text-align: left; padding: 15px; border-bottom: 1px solid var(--border); }}
        .results-table th {{ color: var(--text-muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; white-space: nowrap; }}
        .results-table td {{ font-size: 14px; }}
        .results-table tr:hover td {{ background-color: var(--hover); }}
        
        /* Tags */
        .tag-pill {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-weight: 700; font-size: 10px; letter-spacing: 0.5px; }}
        .tag-cloud {{ background-color: var(--cloud-bg); color: var(--cloud); border: 1px solid var(--cloud); }}
        .tag-primary {{ background-color: var(--primary-bg); color: var(--primary); border: 1px solid var(--primary); }}
        .tag-archive {{ background-color: var(--archive-bg); color: var(--archive); border: 1px solid var(--archive); }}
        
        .play-link {{ color: var(--primary); text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 5px; }}
        .play-link:hover {{ text-decoration: underline; }}

        /* Top Header Box */
        .header-box {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }}
        .header-left h1 {{ margin: 0; font-size: 22px; display: flex; align-items: center; gap: 10px; color: var(--text); }}
        .header-left p {{ margin: 5px 0 0 35px; color: var(--text-muted); font-size: 13px; font-weight: 500; }}
        .theme-toggle {{ background: var(--card-bg); border: 1px solid var(--border); color: var(--text); padding: 10px; border-radius: 50%; cursor: pointer; font-size: 18px; width: 45px; height: 45px; display: flex; justify-content: center; align-items: center; }}

        .pagination {{ display: none; justify-content: center; gap: 15px; margin-top: 25px; }}
        .pagination button {{ padding: 10px 20px; background: var(--bg); color: var(--text); border-radius: 8px; border: 1px solid var(--border); cursor: pointer; font-weight: 600; }}
        .pagination button:hover {{ background: var(--hover); border-color: var(--primary); color: var(--primary); }}
    </style>
    {THEME_SCRIPT}
    </head><body>
    
    <div class="container">
        
        <div class="header-box">
            <div class="header-left">
                <h1><i class="fas fa-layer-group" style="color: var(--primary);"></i> Control Center</h1>
                <p>Bot Management & Database Search</p>
            </div>
            <button class="theme-toggle" onclick="toggleTheme()"><i id="theme-icon" class="fas fa-sun"></i></button>
        </div>
        
        <div class="dashboard-container">
            <div class="dashboard-box db-total">
                <div class="icon-box"><i class="fas fa-database"></i></div>
                <div class="text-box"><h3>Total Files</h3><p>{stats['total']}</p></div>
            </div>
            <div class="dashboard-box db-primary">
                <div class="icon-box"><i class="fas fa-folder"></i></div>
                <div class="text-box"><h3>Primary DB</h3><p>{stats['primary']}</p></div>
            </div>
            <div class="dashboard-box db-cloud">
                <div class="icon-box"><i class="fas fa-cloud"></i></div>
                <div class="text-box"><h3>Cloud DB</h3><p>{stats['cloud']}</p></div>
            </div>
            <div class="dashboard-box db-archive">
                <div class="icon-box"><i class="fas fa-archive"></i></div>
                <div class="text-box"><h3>Archive DB</h3><p>{stats['archive']}</p></div>
            </div>
        </div>

        <div class="search-area">
            <div class="search-form">
                <select id="colSelect">
                    <option value="all">🌍 All Sources</option>
                    <option value="primary">📁 Primary ({stats['primary']})</option>
                    <option value="cloud">☁️ Cloud ({stats['cloud']})</option>
                    <option value="archive">📦 Archive ({stats['archive']})</option>
                </select>
                <input type="text" id="q" placeholder="Enter file name to search..." onkeypress="if(event.key === 'Enter') search(0)">
                <button class="btn-search" onclick="search(0)"><i class="fas fa-search"></i> Search</button>
            </div>
            
            <div class="results-header" id="results-info"></div>
            
            <div class="table-container">
                <table class="results-table" id="results-table" style="display: none;">
                    <thead>
                        <tr>
                            <th>File Name</th>
                            <th style="width: 15%;">Size</th>
                            <th style="width: 15%; text-align: center;">Source</th>
                            <th style="width: 10%; text-align: center;">Action</th>
                        </tr>
                    </thead>
                    <tbody id="results-body"></tbody>
                </table>
                <div id="no-results" style="display:none; text-align:center; padding:40px; color:var(--text-muted);">
                    <i class="fas fa-box-open" style="font-size:40px; margin-bottom:15px;"></i><br><h3>No files found!</h3>
                </div>
            </div>

            <div class="pagination" id="page-box">
                <button id="pBtn" onclick="prev()"><i class="fas fa-chevron-left"></i> Prev</button>
                <button id="nBtn" onclick="next()">Next <i class="fas fa-chevron-right"></i></button>
            </div>
        </div>
    </div>

    <script>
    document.getElementById('theme-icon').className = document.documentElement.getAttribute('data-theme') === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    let curQ = "", curOff = 0, nextOff = "";

    async function search(off) {{
        let q = document.getElementById('q').value;
        let col = document.getElementById('colSelect').value;
        if(!q) return;
        
        curQ = q; curOff = off; 
        
        let res = await fetch(`/api/search?q=${{encodeURIComponent(q)}}&offset=${{off}}&col=${{col}}`);
        let data = await res.json();
        
        document.getElementById('results-info').style.display = 'flex';
        document.getElementById('results-info').innerHTML = `<i class="fas fa-check-circle" style="margin-right:8px;"></i> Found ${{data.total}} matching files`;

        if(data.results.length > 0) {{
            document.getElementById('results-table').style.display = 'table';
            document.getElementById('no-results').style.display = 'none';
            
            let out = "";
            data.results.forEach(f => {{
                let badgeClass = 'tag-primary';
                if(f.source.toLowerCase() === 'cloud') badgeClass = 'tag-cloud';
                else if(f.source.toLowerCase() === 'archive') badgeClass = 'tag-archive';
                
                out += `
                <tr>
                    <td style="word-break: break-all; font-weight: 500;">${{f.name}}</td>
                    <td style="white-space: nowrap; color: var(--text-muted); font-family: monospace;">${{f.size}}</td>
                    <td style="text-align: center;"><span class="tag-pill ${{badgeClass}}">${{f.source.toUpperCase()}}</span></td>
                    <td style="text-align: center;">
                        <a href="${{f.watch}}" target="_blank" class="play-link"><i class="fas fa-play-circle"></i> Play</a>
                    </td>
                </tr>`;
            }});
            document.getElementById('results-body').innerHTML = out;
        }} else {{
            document.getElementById('results-table').style.display = 'none';
            document.getElementById('no-results').style.display = 'block';
        }}
        
        nextOff = data.next_offset;
        document.getElementById('page-box').style.display = 'flex';
        document.getElementById('pBtn').style.display = off > 0 ? 'block' : 'none';
        document.getElementById('nBtn').style.display = nextOff ? 'block' : 'none';
    }}

    function next() {{ if(nextOff) search(nextOff); window.scrollTo(0,0); }}
    function prev() {{ search(Math.max(0, curOff-20)); window.scrollTo(0,0); }}
    </script>
    </body></html>
    """
    return web.Response(text=html, content_type='text/html')
