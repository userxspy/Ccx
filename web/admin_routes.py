from aiohttp import web
import time
import uuid
from info import ADMIN_USERNAME, ADMIN_PASSWORD, ADMINS
from utils import temp, get_size
from database.users_chats_db import db as user_db
from database.ia_filterdb import db_count_documents, get_search_results, COLLECTIONS
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_routes = web.RouteTableDef()

def is_logged_in(request):
    session_id = request.cookies.get('admin_session')
    if not hasattr(temp, 'ADMIN_SESSIONS'): return False
    return session_id in temp.ADMIN_SESSIONS and time.time() < temp.ADMIN_SESSIONS[session_id]

# Shared Theme Script to prevent flickering
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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {{ --bg: #0f0f1a; --box-bg: #1a1a2e; --text: #ffffff; --input-bg: #16213e; --border: #333; --primary: #00d2ff; --btn-text: #0f0f1a; }}
        [data-theme="light"] {{ --bg: #f0f2f5; --box-bg: #ffffff; --text: #333333; --input-bg: #f9f9f9; --border: #dddddd; --primary: #007bff; --btn-text: #ffffff; }}
        body {{ font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: var(--bg); margin: 0; color: var(--text); transition: all 0.3s ease; }}
        .box {{ background: var(--box-bg); padding: 40px 30px; border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.2); width: 100%; max-width: 320px; text-align: center; transition: all 0.3s ease; position: relative; }}
        .theme-btn {{ position: absolute; top: 15px; right: 15px; background: none; border: none; color: var(--text); font-size: 20px; cursor: pointer; outline: none; }}
        h2 {{ margin-top: 0; margin-bottom: 25px; font-weight: 600; letter-spacing: 1px; }}
        input {{ width: 100%; padding: 14px; margin: 10px 0; border: 1px solid var(--border); border-radius: 10px; background: var(--input-bg); color: var(--text); box-sizing: border-box; outline: none; transition: 0.3s; font-size: 15px; }}
        input:focus {{ border-color: var(--primary); box-shadow: 0 0 8px rgba(0, 210, 255, 0.3); }}
        button[type="submit"] {{ width: 100%; padding: 14px; background: var(--primary); color: var(--btn-text); border: none; border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 16px; margin-top: 15px; transition: 0.3s; }}
        button[type="submit"]:hover {{ opacity: 0.9; transform: translateY(-2px); }}
    </style>
    {THEME_SCRIPT}
    </head><body>
    <div class="box">
        <button class="theme-btn" onclick="toggleTheme()"><i id="theme-icon" class="fas fa-sun"></i></button>
        <h2><i class="fas fa-lock" style="color: var(--primary);"></i> Admin Login</h2>
        <form action="/login" method="post">
            <input type="text" name="user" placeholder="Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button type="submit">Secure Login</button>
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
            btn = [[InlineKeyboardButton("🛑 Disconnect Web Session", callback_data=f"logout_{session_id}")]]
            await temp.BOT.send_message(
                chat_id=ADMINS[0], text="✅ **Web Login Detected!**\n\nYour session is active for 1 hour.", reply_markup=InlineKeyboardMarkup(btn)
            )
        except: pass
        return res
    return web.Response(text="<html><body style='background:#0f0f1a;color:#dc3545;text-align:center;padding:50px;font-family:sans-serif;'><h2>❌ Wrong Credentials!</h2><a href='/admin' style='color:#00d2ff;text-decoration:none;font-weight:bold;'>Try Again</a></body></html>", content_type='text/html')

@admin_routes.post('/api/edit_file')
async def edit_file_api(request):
    if not is_logged_in(request): return web.json_response({"err": "no"}, status=403)
    data = await request.json()
    fid, name = data.get('id'), data.get('name')
    for col in COLLECTIONS.values():
        res = await col.update_one({"_id": fid}, {"$set": {"file_name": name}})
        if res.modified_count > 0: return web.json_response({"status": "success"})
    return web.json_response({"status": "fail"})

@admin_routes.post('/api/delete_file')
async def delete_file_api(request):
    if not is_logged_in(request): return web.json_response({"err": "no"}, status=403)
    data = await request.json()
    fid = data.get('id')
    for col in COLLECTIONS.values():
        res = await col.delete_one({"_id": fid})
        if res.deleted_count > 0: return web.json_response({"status": "success"})
    return web.json_response({"status": "fail"})

@admin_routes.get('/dashboard')
async def admin_dashboard(request):
    if not is_logged_in(request): return web.HTTPFound('/admin')
    stats = await db_count_documents()
    total_u = await user_db.total_users_count()

    html = f"""
    <!DOCTYPE html><html><head>
    <title>Admin Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {{ --bg: #0f0f1a; --card-bg: #1a1a2e; --text: #ffffff; --text-muted: #a0a0b0; --primary: #00d2ff; --input-bg: #16213e; --border: #333; --btn-text: #0f0f1a; --modal-bg: rgba(0,0,0,0.8); --drop-bg: #1a1a2e; --drop-hov: #2a2a4e; }}
        [data-theme="light"] {{ --bg: #f4f7f6; --card-bg: #ffffff; --text: #333333; --text-muted: #666666; --primary: #007bff; --input-bg: #ffffff; --border: #dddddd; --btn-text: #ffffff; --modal-bg: rgba(0,0,0,0.5); --drop-bg: #ffffff; --drop-hov: #f0f0f0; }}
        
        body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 15px; transition: all 0.3s ease; }}
        .container {{ max-width: 900px; margin: auto; }}
        
        .header {{ display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 20px 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border: 1px solid var(--border); transition: 0.3s; }}
        .header h1 {{ margin: 0; font-size: 24px; display: flex; align-items: center; gap: 10px; }}
        .header p {{ margin: 5px 0 0; color: var(--text-muted); font-size: 14px; }}
        .theme-btn {{ background: var(--input-bg); border: 1px solid var(--border); color: var(--text); padding: 10px 15px; border-radius: 50px; cursor: pointer; font-size: 16px; transition: 0.3s; outline:none; }}
        
        .search-box {{ display: flex; gap: 10px; margin-bottom: 25px; flex-wrap: wrap; background: var(--card-bg); padding: 15px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border: 1px solid var(--border); transition: 0.3s; }}
        .search-box select, .search-box input {{ padding: 14px 20px; border-radius: 10px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); outline: none; font-size: 15px; transition: 0.3s; }}
        .search-box select {{ font-weight: bold; cursor: pointer; color: var(--primary); }}
        .search-box input {{ flex: 1; min-width: 200px; }}
        .search-box input:focus, .search-box select:focus {{ border-color: var(--primary); }}
        .search-box button {{ padding: 14px 25px; border-radius: 10px; border: none; background: var(--primary); color: var(--btn-text); font-weight: bold; cursor: pointer; font-size: 15px; transition: 0.3s; }}
        .search-box button:hover {{ opacity: 0.9; transform: translateY(-2px); }}
        
        #results-info {{ color: var(--primary); font-weight: bold; margin-bottom: 15px; display: none; text-align: center; font-size: 16px; }}
        
        .card {{ background: var(--card-bg); padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid var(--border); border-left: 5px solid var(--primary); position: relative; transition: transform 0.2s ease; }}
        .card:hover {{ transform: scale(1.01); }}
        .card-title {{ font-weight: 600; margin-bottom: 10px; font-size: 16px; line-height: 1.5; word-break: break-all; padding-right: 60px; }}
        .card-meta {{ font-size: 13px; color: var(--text-muted); margin-bottom: 15px; display:flex; gap:15px; }}
        .source-badge {{ position: absolute; top: 15px; right: 15px; background: var(--input-bg); color: var(--primary); padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; border: 1px solid var(--border); text-transform: uppercase; }}
        
        .btn-group {{ display: flex; gap: 10px; }}
        .btn-play {{ flex: 1; background: #28a745; color: white; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; transition: 0.2s; }}
        .btn-play:hover {{ background: #218838; }}
        
        .btn-action {{ background: var(--input-bg); color: var(--text); padding: 12px 20px; border-radius: 8px; cursor: pointer; border: 1px solid var(--border); font-weight: bold; transition: 0.2s; }}
        .btn-action:hover {{ border-color: var(--primary); color: var(--primary); }}
        
        .dropdown {{ display: none; position: absolute; right: 0; top: 55px; background: var(--drop-bg); border-radius: 10px; min-width: 130px; box-shadow: 0 8px 25px rgba(0,0,0,0.3); border: 1px solid var(--border); z-index: 10; overflow: hidden; }}
        .dropdown button {{ display: block; width: 100%; padding: 12px 15px; border: none; background: none; text-align: left; cursor: pointer; font-size: 14px; color: var(--text); transition: 0.2s; }}
        .dropdown button:hover {{ background: var(--drop-hov); padding-left: 20px; }}
        .drop-del {{ color: #dc3545 !important; font-weight: bold; border-top: 1px solid var(--border) !important; }}

        .pagination {{ display: none; justify-content: center; gap: 15px; margin-top: 30px; margin-bottom: 40px; }}
        .pagination button {{ padding: 12px 25px; background: var(--card-bg); color: var(--text); border-radius: 10px; border: 1px solid var(--border); cursor: pointer; font-weight: bold; transition: 0.2s; }}
        .pagination button:hover {{ background: var(--primary); color: var(--btn-text); border-color: var(--primary); transform: translateY(-2px); }}
        
        #editModal {{ display: none; position: fixed; top:0; left:0; width:100%; height:100%; background: var(--modal-bg); justify-content: center; align-items: center; z-index: 100; backdrop-filter: blur(5px); }}
        .modal-content {{ background: var(--card-bg); padding: 30px; border-radius: 15px; width: 90%; max-width: 450px; color: var(--text); border: 1px solid var(--border); box-shadow: 0 15px 35px rgba(0,0,0,0.3); }}
        .modal-content h3 {{ margin-top:0; color: var(--primary); }}
        .modal-content input {{ width: 100%; padding: 14px; margin: 15px 0 25px; border: 1px solid var(--border); border-radius: 10px; background: var(--input-bg); color: var(--text); box-sizing: border-box; outline:none; font-size:15px; }}
        .modal-content input:focus {{ border-color: var(--primary); }}
        .modal-btn {{ flex: 1; border: none; padding: 14px; border-radius: 10px; font-weight: bold; cursor: pointer; font-size:15px; transition: 0.2s; }}
    </style>
    {THEME_SCRIPT}
    </head><body>
    
    <div class="container">
        <div class="header">
            <div>
                <h1><i class="fas fa-robot" style="color: var(--primary);"></i> Admin Panel</h1>
                <p><i class="fas fa-database"></i> Files: <b>{stats['total']}</b> &nbsp;|&nbsp; <i class="fas fa-users"></i> Users: <b>{total_u}</b></p>
            </div>
            <button class="theme-btn" onclick="toggleTheme()"><i id="theme-icon" class="fas fa-sun"></i></button>
        </div>

        <div class="search-box">
            <select id="colSelect">
                <option value="all">🌍 All Database</option>
                <option value="primary">📁 Primary</option>
                <option value="cloud">☁️ Cloud</option>
                <option value="archive">📦 Archive</option>
            </select>
            <input type="text" id="q" placeholder="Enter file name to search..." onkeypress="if(event.key === 'Enter') search(0)">
            <button onclick="search(0)"><i class="fas fa-search"></i> Search</button>
        </div>
        
        <div id="results-info"></div>
        <div id="results"></div>

        <div class="pagination" id="page-box">
            <button id="pBtn" onclick="prev()"><i class="fas fa-chevron-left"></i> Previous</button>
            <button id="nBtn" onclick="next()">Next <i class="fas fa-chevron-right"></i></button>
        </div>
    </div>

    <div id="editModal"><div class="modal-content">
        <h3><i class="fas fa-edit"></i> Edit File Name</h3>
        <input type="text" id="newName">
        <input type="hidden" id="editFid">
        <div style="display:flex; gap:15px;">
            <button class="modal-btn" onclick="saveEdit()" style="background:#28a745; color:white;">Update</button>
            <button class="modal-btn" onclick="closeModal()" style="background:var(--input-bg); color:var(--text); border:1px solid var(--border);">Cancel</button>
        </div>
    </div></div>

    <script>
    document.getElementById('theme-icon').className = document.documentElement.getAttribute('data-theme') === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    let curQ = "", curOff = 0, nextOff = "", curCol = "all";

    async function search(off) {{
        let q = document.getElementById('q').value;
        let col = document.getElementById('colSelect').value;
        if(!q) return;
        
        curQ = q; curOff = off; curCol = col;
        let res = await fetch(`/api/search?q=${{encodeURIComponent(q)}}&offset=${{off}}&col=${{col}}`);
        let data = await res.json();
        
        document.getElementById('results-info').style.display = 'block';
        document.getElementById('results-info').innerHTML = `<i class="fas fa-chart-bar"></i> Found ${{data.total}} matching files`;

        let out = "";
        data.results.forEach(f => {{
            let fid = f.watch.split('file_id=')[1].split('&')[0];
            out += `
            <div class="card" id="row-${{fid}}">
                <span class="source-badge"><i class="fas fa-server"></i> ${{f.source}}</span> 
                <div class="card-title">${{f.name}}</div>
                <div class="card-meta"><span><i class="fas fa-hdd"></i> ${{f.size}}</span> <span><i class="fas fa-file"></i> ${{f.type}}</span></div>
                <div class="btn-group">
                    <a href="${{f.watch}}" target="_blank" class="btn-play"><i class="fas fa-play-circle"></i> Play / View</a>
                    <div style="position:relative">
                        <button class="btn-action" onclick="toggleDrop('${{fid}}')"><i class="fas fa-cog"></i></button>
                        <div class="dropdown" id="drop-${{fid}}">
                            <button onclick="openEdit('${{fid}}', '${{f.name.replace(/'/g, "\\'")}}')"><i class="fas fa-pen"></i> Edit Name</button>
                            <button class="drop-del" onclick="deleteFile('${{fid}}')"><i class="fas fa-trash-alt"></i> Delete File</button>
                        </div>
                    </div>
                </div>
            </div>`;
        }});
        document.getElementById('results').innerHTML = out || "<div class='card' style='text-align:center; padding: 40px;'><i class='fas fa-box-open' style='font-size:40px; color:var(--text-muted); margin-bottom:15px;'></i><br><h3>No files found in this collection.</h3></div>";
        
        nextOff = data.next_offset;
        document.getElementById('page-box').style.display = 'flex';
        document.getElementById('pBtn').style.display = off > 0 ? 'block' : 'none';
        document.getElementById('nBtn').style.display = nextOff ? 'block' : 'none';
    }}

    function toggleDrop(id) {{
        let d = document.getElementById('drop-'+id);
        document.querySelectorAll('.dropdown').forEach(x => {{ if(x.id !== 'drop-'+id) x.style.display = 'none'; }});
        d.style.display = (d.style.display === 'block') ? 'none' : 'block';
    }}

    function openEdit(id, name) {{
        document.getElementById('editFid').value = id;
        document.getElementById('newName').value = name;
        document.getElementById('editModal').style.display = 'flex';
    }}

    function closeModal() {{ document.getElementById('editModal').style.display = 'none'; }}

    async function saveEdit() {{
        let id = document.getElementById('editFid').value;
        let name = document.getElementById('newName').value;
        let res = await fetch('/api/edit_file', {{ method:'POST', body:JSON.stringify({{id: id, name: name}}) }});
        if((await res.json()).status === 'success') {{
            closeModal();
            search(curOff); // Refresh current page silently
        }}
    }}

    async function deleteFile(id) {{
        if(!confirm("⚠️ Delete this file permanently?")) return;
        let res = await fetch('/api/delete_file', {{ method:'POST', body:JSON.stringify({{id: id}}) }});
        if((await res.json()).status === 'success') {{ document.getElementById('row-'+id).remove(); }}
    }}

    function next() {{ if(nextOff) search(nextOff); window.scrollTo(0,0); }}
    function prev() {{ search(Math.max(0, curOff-20)); window.scrollTo(0,0); }}
    
    // Close dropdowns when clicking outside
    window.onclick = function(event) {{
        if (!event.target.matches('.btn-action') && !event.target.matches('.fas.fa-cog')) {{
            document.querySelectorAll('.dropdown').forEach(x => x.style.display = 'none');
        }}
    }}
    </script>
    </body></html>
    """
    return web.Response(text=html, content_type='text/html')
