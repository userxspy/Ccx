from aiohttp import web
import time
import uuid
import json
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
        updateChartTheme(newTheme);
    }
</script>
"""

@admin_routes.get('/admin')
async def login_page(request):
    html = f"""
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {{ --bg: #0f0f1a; --box-bg: rgba(26, 26, 46, 0.7); --text: #ffffff; --input-bg: rgba(22, 33, 62, 0.8); --border: rgba(255,255,255,0.1); --primary: #00d2ff; --btn-text: #0f0f1a; }}
        [data-theme="light"] {{ --bg: #f4f7f6; --box-bg: rgba(255, 255, 255, 0.8); --text: #333333; --input-bg: rgba(249, 249, 249, 0.8); --border: rgba(0,0,0,0.1); --primary: #007bff; --btn-text: #ffffff; }}
        body {{ font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: var(--bg); margin: 0; color: var(--text); transition: all 0.3s ease; }}
        /* Glassmorphism Box */
        .box {{ background: var(--box-bg); padding: 40px 30px; border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.2); width: 100%; max-width: 320px; text-align: center; backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); border: 1px solid var(--border); position: relative; }}
        .theme-btn {{ position: absolute; top: 15px; right: 15px; background: none; border: none; color: var(--text); font-size: 20px; cursor: pointer; outline: none; }}
        h2 {{ margin-top: 0; margin-bottom: 25px; font-weight: 600; letter-spacing: 1px; }}
        input {{ width: 100%; padding: 14px; margin: 10px 0; border: 1px solid var(--border); border-radius: 10px; background: var(--input-bg); color: var(--text); box-sizing: border-box; outline: none; transition: 0.3s; font-size: 15px; }}
        input:focus {{ border-color: var(--primary); box-shadow: 0 0 8px rgba(0, 210, 255, 0.3); }}
        button[type="submit"] {{ width: 100%; padding: 14px; background: var(--primary); color: var(--btn-text); border: none; border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 16px; margin-top: 15px; transition: 0.3s; }}
        button[type="submit"]:hover {{ opacity: 0.9; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 210, 255, 0.4); }}
    </style>
    {THEME_SCRIPT}
    </head><body>
    <div class="box">
        <button class="theme-btn" onclick="toggleTheme()"><i id="theme-icon" class="fas fa-sun"></i></button>
        <h2><i class="fas fa-fingerprint" style="color: var(--primary);"></i> Secure Login</h2>
        <form action="/login" method="post">
            <input type="text" name="user" placeholder="Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button type="submit">Login to Dashboard</button>
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
            await temp.BOT.send_message(chat_id=ADMINS[0], text="✅ **Web Login Detected!**\n\nYour session is active for 1 hour.", reply_markup=InlineKeyboardMarkup(btn))
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
    <title>Ultimate Admin Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        :root {{ --bg: #0f0f1a; --card-bg: rgba(26, 26, 46, 0.6); --text: #ffffff; --text-muted: #a0a0b0; --primary: #00d2ff; --input-bg: rgba(22, 33, 62, 0.6); --border: rgba(255,255,255,0.1); --btn-text: #0f0f1a; --drop-bg: #1a1a2e; }}
        [data-theme="light"] {{ --bg: #f0f2f5; --card-bg: rgba(255, 255, 255, 0.7); --text: #333333; --text-muted: #666666; --primary: #007bff; --input-bg: rgba(249, 249, 249, 0.7); --border: rgba(0,0,0,0.1); --btn-text: #ffffff; --drop-bg: #ffffff; }}
        
        body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 15px; transition: all 0.3s ease; }}
        .container {{ max-width: 1000px; margin: auto; }}
        
        /* Glassmorphism Global */
        .glass {{ background: var(--card-bg); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid var(--border); box-shadow: 0 8px 32px rgba(0,0,0,0.1); border-radius: 15px; }}
        
        .header {{ display: flex; justify-content: space-between; align-items: center; padding: 20px 25px; margin-bottom: 25px; }}
        .header h1 {{ margin: 0; font-size: 24px; display: flex; align-items: center; gap: 10px; }}
        .header p {{ margin: 5px 0 0; color: var(--text-muted); font-size: 14px; }}
        .btn-icon {{ background: var(--input-bg); border: 1px solid var(--border); color: var(--text); padding: 10px 15px; border-radius: 50px; cursor: pointer; font-size: 16px; transition: 0.3s; outline:none; margin-left: 10px; }}
        .btn-icon:hover {{ color: var(--primary); border-color: var(--primary); }}
        
        /* Chart Section */
        .chart-container {{ display: flex; justify-content: center; margin-bottom: 25px; padding: 20px; }}
        .chart-wrapper {{ width: 100%; max-width: 300px; }}
        
        .search-box {{ display: flex; gap: 10px; margin-bottom: 25px; padding: 15px; flex-wrap: wrap; }}
        .search-box select, .search-box input {{ padding: 14px 20px; border-radius: 10px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); outline: none; font-size: 15px; transition: 0.3s; }}
        .search-box input {{ flex: 1; min-width: 200px; }}
        .search-box input:focus {{ border-color: var(--primary); box-shadow: 0 0 10px rgba(0, 210, 255, 0.2); }}
        .search-box button {{ padding: 14px 25px; border-radius: 10px; border: none; background: var(--primary); color: var(--btn-text); font-weight: bold; cursor: pointer; transition: 0.3s; }}
        .search-box button:hover {{ opacity: 0.9; transform: translateY(-2px); }}
        
        #results-info {{ color: var(--primary); font-weight: bold; margin-bottom: 15px; text-align: center; font-size: 16px; }}
        
        /* Grid Layout */
        .results-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }}
        .results-list {{ display: flex; flex-direction: column; gap: 10px; }}
        
        .card {{ padding: 20px; position: relative; transition: transform 0.2s ease; border-left: 4px solid var(--primary); }}
        .card:hover {{ transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }}
        .card-title {{ font-weight: 600; margin-bottom: 10px; font-size: 15px; line-height: 1.4; word-break: break-all; padding-right: 60px; }}
        .card-meta {{ font-size: 12px; color: var(--text-muted); margin-bottom: 15px; display:flex; gap:15px; }}
        .source-badge {{ position: absolute; top: 15px; right: 15px; background: var(--input-bg); color: var(--primary); padding: 4px 8px; border-radius: 6px; font-size: 10px; font-weight: bold; border: 1px solid var(--border); text-transform: uppercase; }}
        
        .btn-group {{ display: flex; gap: 10px; }}
        .btn-play {{ flex: 1; background: #28a745; color: white; text-align: center; padding: 10px; border-radius: 8px; text-decoration: none; font-weight: bold; transition: 0.2s; }}
        .btn-play:hover {{ background: #218838; }}
        .btn-action {{ background: var(--input-bg); color: var(--text); padding: 10px 15px; border-radius: 8px; cursor: pointer; border: 1px solid var(--border); transition: 0.2s; }}
        .btn-action:hover {{ border-color: var(--primary); color: var(--primary); }}
        
        /* Skeleton Animation */
        .skeleton {{ animation: shimmer 1.5s infinite linear; background: linear-gradient(to right, var(--input-bg) 4%, var(--border) 25%, var(--input-bg) 36%); background-size: 1000px 100%; border-radius: 8px; }}
        .skel-title {{ height: 20px; width: 80%; margin-bottom: 10px; }}
        .skel-meta {{ height: 12px; width: 50%; margin-bottom: 15px; }}
        .skel-btn {{ height: 35px; width: 100%; }}
        @keyframes shimmer {{ 0% {{ background-position: -1000px 0; }} 100% {{ background-position: 1000px 0; }} }}

        .pagination {{ display: none; justify-content: center; gap: 15px; margin: 30px 0; }}
        .pagination button {{ padding: 12px 25px; color: var(--text); cursor: pointer; font-weight: bold; transition: 0.2s; }}
        .pagination button:hover {{ background: var(--primary); color: var(--btn-text); border-color: var(--primary); }}
        
        /* SweetAlert Custom Theme */
        .swal2-popup {{ background: var(--bg) !important; color: var(--text) !important; border: 1px solid var(--border); border-radius: 15px !important; }}
        .swal2-input {{ background: var(--input-bg) !important; color: var(--text) !important; border: 1px solid var(--border) !important; }}
    </style>
    {THEME_SCRIPT}
    </head><body>
    
    <div class="container">
        <div class="glass header">
            <div>
                <h1><i class="fas fa-layer-group" style="color: var(--primary);"></i> Control Center</h1>
                <p><i class="fas fa-database"></i> Total DB: <b>{stats['total']}</b> &nbsp;|&nbsp; <i class="fas fa-users"></i> Users: <b>{total_u}</b></p>
            </div>
            <div>
                <button class="btn-icon" onclick="toggleLayout()" title="Toggle Grid/List"><i id="layout-icon" class="fas fa-list"></i></button>
                <button class="btn-icon" onclick="toggleTheme()" title="Toggle Theme"><i id="theme-icon" class="fas fa-sun"></i></button>
            </div>
        </div>

        <div class="glass chart-container">
            <div class="chart-wrapper">
                <canvas id="dbChart"></canvas>
            </div>
        </div>

        <div class="glass search-box">
            <select id="colSelect">
                <option value="all">🌍 All Sources</option>
                <option value="primary">📁 Primary ({stats['primary']})</option>
                <option value="cloud">☁️ Cloud ({stats['cloud']})</option>
                <option value="archive">📦 Archive ({stats['archive']})</option>
            </select>
            <input type="text" id="q" placeholder="Enter file name to search..." onkeypress="if(event.key === 'Enter') search(0)">
            <button onclick="search(0)"><i class="fas fa-search"></i> Search</button>
        </div>
        
        <div id="results-info"></div>
        <div id="results" class="results-grid"></div>

        <div class="pagination" id="page-box">
            <button class="glass" id="pBtn" onclick="prev()"><i class="fas fa-chevron-left"></i> Prev</button>
            <button class="glass" id="nBtn" onclick="next()">Next <i class="fas fa-chevron-right"></i></button>
        </div>
    </div>

    <script>
    // --- 1. CHART.JS INITIALIZATION ---
    let myChart;
    function initChart() {{
        const ctx = document.getElementById('dbChart').getContext('2d');
        const textColor = document.documentElement.getAttribute('data-theme') === 'dark' ? '#ffffff' : '#333333';
        
        myChart = new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: ['Primary', 'Cloud', 'Archive'],
                datasets: [{{
                    data: [{stats['primary']}, {stats['cloud']}, {stats['archive']}],
                    backgroundColor: ['#00d2ff', '#28a745', '#ffc107'],
                    borderWidth: 0, hoverOffset: 5
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ position: 'bottom', labels: {{ color: textColor }} }} }}
            }}
        }});
    }}
    initChart();

    function updateChartTheme(theme) {{
        if(myChart) {{
            myChart.options.plugins.legend.labels.color = theme === 'dark' ? '#ffffff' : '#333333';
            myChart.update();
        }}
    }}

    // --- 2. GRID / LIST TOGGLE ---
    let isGrid = true;
    function toggleLayout() {{
        isGrid = !isGrid;
        const resDiv = document.getElementById('results');
        const icon = document.getElementById('layout-icon');
        if(isGrid) {{ resDiv.className = 'results-grid'; icon.className = 'fas fa-list'; }} 
        else {{ resDiv.className = 'results-list'; icon.className = 'fas fa-th-large'; }}
    }}

    // --- 3. SEARCH & SKELETON LOADER ---
    let curQ = "", curOff = 0, nextOff = "";

    function showSkeleton() {{
        let skelHTML = '';
        for(let i=0; i<6; i++) {{
            skelHTML += `
            <div class="glass card">
                <div class="skeleton skel-title"></div>
                <div class="skeleton skel-meta"></div>
                <div class="skeleton skel-btn"></div>
            </div>`;
        }}
        document.getElementById('results').innerHTML = skelHTML;
        document.getElementById('page-box').style.display = 'none';
        document.getElementById('results-info').innerText = '⏳ Searching Database...';
        document.getElementById('results-info').style.display = 'block';
    }}

    async function search(off) {{
        let q = document.getElementById('q').value;
        let col = document.getElementById('colSelect').value;
        if(!q) return;
        
        curQ = q; curOff = off; 
        showSkeleton(); // Show fancy loader
        
        let res = await fetch(`/api/search?q=${{encodeURIComponent(q)}}&offset=${{off}}&col=${{col}}`);
        let data = await res.json();
        
        document.getElementById('results-info').innerHTML = `<i class="fas fa-check-circle"></i> Found ${{data.total}} matching files`;

        let out = "";
        data.results.forEach(f => {{
            let fid = f.watch.split('file_id=')[1].split('&')[0];
            out += `
            <div class="glass card" id="row-${{fid}}">
                <span class="source-badge">${{f.source}}</span> 
                <div class="card-title">${{f.name}}</div>
                <div class="card-meta"><span><i class="fas fa-hdd"></i> ${{f.size}}</span> <span><i class="fas fa-file"></i> ${{f.type}}</span></div>
                <div class="btn-group">
                    <a href="${{f.watch}}" target="_blank" class="btn-play"><i class="fas fa-play"></i> Watch</a>
                    <button class="btn-action" onclick="openEdit('${{fid}}', '${{f.name.replace(/'/g, "\\'")}}')"><i class="fas fa-pen"></i></button>
                    <button class="btn-action" style="color:#dc3545;" onclick="deleteFile('${{fid}}')"><i class="fas fa-trash"></i></button>
                </div>
            </div>`;
        }});
        
        document.getElementById('results').innerHTML = out || "<div class='glass card' style='text-align:center; padding: 40px;'><h3>❌ No files found!</h3></div>";
        nextOff = data.next_offset;
        document.getElementById('page-box').style.display = 'flex';
        document.getElementById('pBtn').style.display = off > 0 ? 'block' : 'none';
        document.getElementById('nBtn').style.display = nextOff ? 'block' : 'none';
    }}

    // --- 4. SWEET ALERT INTEGRATIONS ---
    function showToast(icon, title) {{
        Swal.fire({{ toast: true, position: 'top-end', icon: icon, title: title, showConfirmButton: false, timer: 3000, timerProgressBar: true }});
    }}

    async function openEdit(id, oldName) {{
        const {{ value: newName }} = await Swal.fire({{
            title: 'Edit File Name', input: 'text', inputValue: oldName,
            showCancelButton: true, confirmButtonText: 'Save Changes', confirmButtonColor: '#28a745'
        }});
        
        if (newName && newName !== oldName) {{
            let res = await fetch('/api/edit_file', {{ method:'POST', body:JSON.stringify({{id: id, name: newName}}) }});
            if((await res.json()).status === 'success') {{
                showToast('success', 'File renamed successfully!');
                search(curOff); // Refresh silently
            }} else {{ showToast('error', 'Failed to rename file.'); }}
        }}
    }}

    async function deleteFile(id) {{
        const result = await Swal.fire({{
            title: 'Are you sure?', text: "You won't be able to revert this!", icon: 'warning',
            showCancelButton: true, confirmButtonColor: '#dc3545', confirmButtonText: 'Yes, delete it!'
        }});
        
        if (result.isConfirmed) {{
            let res = await fetch('/api/delete_file', {{ method:'POST', body:JSON.stringify({{id: id}}) }});
            if((await res.json()).status === 'success') {{ 
                document.getElementById('row-'+id).remove();
                showToast('success', 'File deleted permanently!');
            }} else {{ showToast('error', 'Failed to delete file.'); }}
        }}
    }}

    function next() {{ if(nextOff) search(nextOff); window.scrollTo(0,0); }}
    function prev() {{ search(Math.max(0, curOff-20)); window.scrollTo(0,0); }}
    </script>
    </body></html>
    """
    return web.Response(text=html, content_type='text/html')
