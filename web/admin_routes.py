from aiohttp import web
import time
import uuid
from info import ADMIN_USERNAME, ADMIN_PASSWORD, ADMINS
from utils import temp
from database.users_chats_db import db as user_db
from database.ia_filterdb import db_count_documents, COLLECTIONS
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_routes = web.RouteTableDef()

def safe_html_response(html: str) -> web.Response:
    clean = html.encode('utf-8', errors='replace').decode('utf-8')
    return web.Response(text=clean, content_type='text/html', charset='utf-8')

def is_logged_in(request):
    session_id = request.cookies.get('admin_session')
    if not hasattr(temp, 'ADMIN_SESSIONS'): return False
    return session_id in temp.ADMIN_SESSIONS and time.time() < temp.ADMIN_SESSIONS[session_id]

# ---------------------------------------------
# SHARED ASSETS
# ---------------------------------------------
SHARED_HEAD = r"""
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#08090d;--bg2:#0f1117;--bg3:#161821;--bg4:#1e2030;
  --accent:#5fffb0;--accent2:#00b8ff;--accent3:#ff6b6b;
  --text:#e8eaf2;--muted:#5a5f7a;--border:#252838;--card:#13151f;
  --shadow:rgba(0,0,0,0.5);--sidebar-w:260px;
}
body.light{
  --bg:#f0f2f5;--bg2:#ffffff;--bg3:#e8eaef;--bg4:#dde0e8;
  --text:#1a1c24;--muted:#6b7099;--border:#cdd0de;--card:#ffffff;
  --shadow:rgba(0,0,0,0.1);
}
body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;transition:background .25s,color .25s;overflow-x:hidden}

/* -- TOPBAR -- */
.topbar{background:var(--bg2);border-bottom:1px solid var(--border);padding:0 16px;display:flex;align-items:center;height:54px;position:sticky;top:0;z-index:100;gap:12px;transition:background .25s,border-color .25s}
.ham-btn{background:none;border:none;cursor:pointer;color:var(--text);display:flex;flex-direction:column;gap:5px;padding:6px;border-radius:6px;transition:background .15s;flex-shrink:0}
.ham-btn:hover{background:var(--bg3)}
.ham-line{display:block;width:20px;height:2px;background:currentColor;border-radius:2px;transition:all .25s}
.ham-btn.open .ham-line:nth-child(1){transform:translateY(7px) rotate(45deg)}
.ham-btn.open .ham-line:nth-child(2){opacity:0;transform:scaleX(0)}
.ham-btn.open .ham-line:nth-child(3){transform:translateY(-7px) rotate(-45deg)}

.logo{font-family:'Space Mono',monospace;font-size:12px;letter-spacing:.06em;color:var(--accent);display:flex;align-items:center;gap:7px;text-decoration:none;flex:1}
.logo-dot{width:7px;height:7px;background:var(--accent);border-radius:50%;box-shadow:0 0 6px var(--accent);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.2}}
.topbar-right{display:flex;align-items:center;gap:8px;margin-left:auto}
.theme-btn{background:var(--bg3);border:1px solid var(--border);border-radius:20px;padding:5px 12px;font-size:11px;color:var(--muted);cursor:pointer;font-family:'Space Mono',monospace;letter-spacing:.04em;transition:all .15s;display:flex;align-items:center;gap:5px}
.theme-btn:hover{border-color:var(--accent);color:var(--text)}

/* -- SIDEBAR -- */
.sidebar-overlay{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:150;opacity:0;pointer-events:none;transition:opacity .25s}
.sidebar-overlay.open{opacity:1;pointer-events:all}
.sidebar{position:fixed;top:0;left:0;height:100%;width:var(--sidebar-w);background:var(--bg2);border-right:1px solid var(--border);z-index:160;display:flex;flex-direction:column;transform:translateX(-100%);transition:transform .28s cubic-bezier(.4,0,.2,1)}
.sidebar.open{transform:translateX(0)}
.sb-header{padding:16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.sb-logo{font-family:'Space Mono',monospace;font-size:11px;color:var(--accent);letter-spacing:.08em;display:flex;align-items:center;gap:7px}
.sb-close{background:none;border:none;cursor:pointer;color:var(--muted);font-size:18px;line-height:1;padding:4px;border-radius:5px;transition:all .15s}
.sb-close:hover{color:var(--text);background:var(--bg3)}

.sb-nav{padding:12px 8px;flex:1}
.sb-section{font-size:9px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;font-family:'Space Mono',monospace;padding:4px 8px 8px}
.sb-link{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:8px;text-decoration:none;color:var(--muted);font-size:14px;font-weight:500;transition:all .15s;margin-bottom:2px;border:1px solid transparent}
.sb-link:hover{background:var(--bg3);color:var(--text)}
.sb-link.active{background:rgba(95,255,176,.1);color:var(--accent);border-color:rgba(95,255,176,.2)}
.sb-icon{font-size:16px;width:22px;text-align:center;flex-shrink:0}
.sb-arrow{margin-left:auto;font-size:11px;opacity:.4}

.sb-footer{padding:12px 8px;border-top:1px solid var(--border)}
.sb-logout{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:8px;text-decoration:none;color:#ff6b6b;font-size:14px;font-weight:500;transition:all .15s;border:1px solid transparent;width:100%;background:none;cursor:pointer;font-family:'DM Sans',sans-serif}
.sb-logout:hover{background:rgba(255,107,107,.1);border-color:rgba(255,107,107,.25)}

/* -- SEARCH ZONE -- */
.search-zone{padding:14px 20px;background:var(--bg2);border-bottom:1px solid var(--border);transition:background .25s}
.search-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.filter-tabs{display:flex;gap:3px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:3px;flex-shrink:0;transition:background .25s}
.ftab{background:none;border:none;padding:6px 12px;border-radius:6px;font-size:12px;color:var(--muted);cursor:pointer;font-family:'DM Sans',sans-serif;transition:all .15s;white-space:nowrap}
.ftab.active{background:var(--bg2);color:var(--text);border:1px solid var(--border);box-shadow:0 1px 3px var(--shadow)}
.search-wrap{flex:1;position:relative;min-width:160px}
.s-icon{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--muted);font-size:14px;pointer-events:none}
.search-input{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:10px 14px 10px 36px;color:var(--text);font-size:14px;font-family:'DM Sans',sans-serif;outline:none;transition:border .2s,background .25s}
.search-input::placeholder{color:var(--muted)}
.search-input:focus{border-color:rgba(95,255,176,.5)}
.search-btn{background:var(--accent);color:#08090d;border:none;border-radius:8px;padding:10px 18px;font-weight:600;font-size:13px;cursor:pointer;font-family:'DM Sans',sans-serif;white-space:nowrap;transition:opacity .15s}
.search-btn:hover{opacity:.85}

/* -- MAIN -- */
.main{padding:20px;max-width:900px;margin:0 auto}

/* STATS */
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px}
@media(max-width:580px){.stats-row{grid-template-columns:repeat(2,1fr)}}
.scard{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 16px;position:relative;overflow:hidden;transition:background .25s,border-color .25s}
.scard::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.scard.green::before{background:var(--accent)}
.scard.blue::before{background:var(--accent2)}
.scard.red::before{background:var(--accent3)}
.scard.amber::before{background:#ffb547}
.scard-label{font-size:10px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase;font-family:'Space Mono',monospace;margin-bottom:8px}
.scard-val{font-size:22px;font-weight:600}
.scard-sub{font-size:11px;color:var(--muted);margin-top:3px}

/* RESULTS */
.results-info{display:none;align-items:center;justify-content:space-between;padding:4px 0 12px}
.results-count{font-family:'Space Mono',monospace;font-size:12px;color:var(--accent)}
.results-hint{font-size:12px;color:var(--muted)}

/* FILE CARDS */
.file-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:15px;display:grid;grid-template-columns:1fr auto;gap:12px;align-items:start;margin-bottom:10px;transition:border-color .2s,transform .15s,background .25s,opacity .3s;animation:slideIn .18s ease both}
@keyframes slideIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.file-card:hover{border-color:rgba(95,255,176,.25);transform:translateY(-1px)}
.fc-top{display:flex;align-items:center;gap:7px;margin-bottom:8px;flex-wrap:wrap}
.source-badge{font-family:'Space Mono',monospace;font-size:10px;padding:2px 8px;border-radius:4px;letter-spacing:.04em}
.source-badge.primary{background:rgba(95,255,176,.1);color:#5fffb0;border:1px solid rgba(95,255,176,.25)}
.source-badge.cloud{background:rgba(0,184,255,.1);color:#00b8ff;border:1px solid rgba(0,184,255,.25)}
.source-badge.archive{background:rgba(255,181,71,.1);color:#ffb547;border:1px solid rgba(255,181,71,.25)}
.type-tag{font-size:11px;color:var(--muted);background:var(--bg4);padding:2px 7px;border-radius:4px;transition:background .25s}
.fc-name{font-size:14px;font-weight:500;line-height:1.4;margin-bottom:6px;word-break:break-word}
.fc-meta{font-size:12px;color:var(--muted);display:flex;gap:14px;flex-wrap:wrap}
.fc-actions{display:flex;flex-direction:column;gap:6px;min-width:88px; justify-content:center;}
.btn-play{background:rgba(95,255,176,.1);border:1px solid rgba(95,255,176,.3);color:#5fffb0;border-radius:7px;padding:9px 15px;font-size:13px;font-weight:600;cursor:pointer;text-align:center;text-decoration:none;display:block;font-family:'DM Sans',sans-serif;transition:background .15s}
.btn-play:hover{background:rgba(95,255,176,.2)}

/* EMPTY */
.empty{text-align:center;padding:56px 20px;color:var(--muted)}
.empty-icon{font-size:28px;margin-bottom:12px;opacity:.3}
.empty p{font-size:14px;line-height:1.7}

/* PAGINATION */
.pagination{display:none;justify-content:center;align-items:center;gap:12px;padding:16px 0 8px}
.pg-btn{background:var(--bg3);border:1px solid var(--border);color:var(--text);border-radius:8px;padding:8px 18px;font-size:13px;cursor:pointer;font-family:'DM Sans',sans-serif;transition:border-color .15s,background .25s}
.pg-btn:hover{border-color:var(--accent)}
.pg-btn:disabled{opacity:.3;cursor:not-allowed}
.pg-info{font-family:'Space Mono',monospace;font-size:11px;color:var(--muted)}

/* TOAST */
.toast{position:fixed;bottom:20px;right:20px;background:var(--bg4);border:1px solid var(--border);border-radius:8px;padding:10px 16px;font-size:13px;z-index:300;transform:translateX(130%);transition:transform .25s;pointer-events:none;box-shadow:0 4px 20px var(--shadow)}
.toast.show{transform:translateX(0)}
.toast.success{border-color:rgba(95,255,176,.4);color:#5fffb0}
.toast.error{border-color:rgba(255,107,107,.4);color:#ff6b6b}

/* LOGIN */
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.login-box{width:100%;max-width:340px}
.login-logo{font-family:'Space Mono',monospace;font-size:12px;color:var(--accent);text-align:center;margin-bottom:28px;letter-spacing:.1em;display:flex;align-items:center;justify-content:center;gap:8px}
.login-card{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:28px;transition:background .25s}
.login-card h2{font-size:18px;font-weight:500;margin-bottom:5px}
.login-card .sub{font-size:13px;color:var(--muted);margin-bottom:22px}
.login-card label{font-size:10px;color:var(--muted);letter-spacing:.05em;text-transform:uppercase;font-family:'Space Mono',monospace;display:block;margin-bottom:6px}
.login-card input[type=text],.login-card input[type=password]{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:11px 14px;color:var(--text);font-size:14px;font-family:'DM Sans',sans-serif;outline:none;margin-bottom:14px;transition:border .2s,background .25s}
.login-card input:focus{border-color:rgba(95,255,176,.4)}
.login-card .submit-btn{width:100%;background:var(--accent);color:#08090d;border:none;border-radius:8px;padding:12px;font-weight:600;font-size:14px;cursor:pointer;font-family:'DM Sans',sans-serif;transition:opacity .15s}
.login-card .submit-btn:hover{opacity:.85}
.err-box{background:rgba(255,107,107,.1);border:1px solid rgba(255,107,107,.3);color:#ff6b6b;border-radius:8px;padding:10px 14px;font-size:13px;margin-bottom:14px}
.theme-corner{position:fixed;top:14px;right:16px;z-index:10}
</style>
"""

THEME_JS = r"""<script>
(function(){if(localStorage.getItem('theme')==='light')document.body.classList.add('light')})();
function toggleTheme(){
  var l=document.body.classList.toggle('light');
  localStorage.setItem('theme',l?'light':'dark');
  var b=document.getElementById('themeBtn');
  if(b){b.querySelector('.ti').innerHTML=l?'&#9661;':'&#9728;';b.querySelector('.tl').textContent=l?'Dark':'Light';}
}
function initThemeBtn(){
  var b=document.getElementById('themeBtn');
  if(!b)return;
  var l=document.body.classList.contains('light');
  b.querySelector('.ti').innerHTML=l?'&#9661;':'&#9728;';
  b.querySelector('.tl').textContent=l?'Dark':'Light';
}
</script>"""

SIDEBAR_HTML = r"""
<div class="sidebar-overlay" id="sbOverlay" onclick="closeSidebar()"></div>
<div class="sidebar" id="sidebar">
  <div class="sb-header">
    <div class="sb-logo"><div class="logo-dot"></div>CINEMATIC_BOT</div>
    <button class="sb-close" onclick="closeSidebar()">&#10005;</button>
  </div>
  <nav class="sb-nav">
    <div class="sb-section">Navigation</div>
    <a href="/dashboard" class="sb-link {active_dash}">
      <span class="sb-icon">&#8862;</span> Dashboard <span class="sb-arrow">&#8250;</span>
    </a>
  </nav>
  <div class="sb-footer">
    <a href="/logout" class="sb-logout"><span class="sb-icon">&#9003;</span> Logout</a>
  </div>
</div>"""

SIDEBAR_JS = r"""<script>
function openSidebar(){
  document.getElementById('sidebar').classList.add('open');
  document.getElementById('sbOverlay').classList.add('open');
  document.getElementById('hamBtn').classList.add('open');
}
function closeSidebar(){
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sbOverlay').classList.remove('open');
  document.getElementById('hamBtn').classList.remove('open');
}
</script>"""

SEARCH_JS = r"""<script>
var curQ='',curOff=0,nextOff='',curCol='all',curPage=1;
function setCol(el){
  document.querySelectorAll('.ftab').forEach(function(t){t.classList.remove('active')});
  el.classList.add('active');curCol=el.dataset.col;
}

function srcClass(src){
  if(!src) return 'primary';
  var s=src.toLowerCase();
  if(s==='primary'||s==='cloud'||s==='archive') return s;
  return 'primary';
}

async function doSearch(off){
  var q=document.getElementById('q').value.trim();
  if(!q){showToast('Search term daalen','error');return;}
  curQ=q;curOff=off;if(off===0)curPage=1;
  
  try {
      var res=await fetch('/api/search?q='+encodeURIComponent(q)+'&offset='+off+'&col='+curCol);
      if(!res.ok){showToast('API Error: '+res.status,'error');return;}
      
      var data=await res.json();
      if(data.error){showToast(data.error,'error');return;}
      
      document.getElementById('resInfo').style.display='flex';
      document.getElementById('resCount').textContent=data.total.toLocaleString()+' result'+(data.total!==1?'s':'')+' \u2014 "'+q+'"';
      
      if(!data.results||!data.results.length){
        document.getElementById('results').innerHTML='<div class="empty"><div class="empty-icon">\u25c8</div><p>No files found in <b>'+curCol+'</b> for \u201c'+q+'\u201d</p></div>';
        document.getElementById('pageBox').style.display='none';return;
      }
      
      var html='';
      data.results.forEach(function(f,i){
        var sc=srcClass(f.source);
        var d=(i*.04)+'s';
        
        html += '<div class="file-card" style="animation-delay:' + d + '">' +
            '<div><div class="fc-top"><span class="source-badge ' + sc + '">' + sc.toUpperCase() + '</span><span class="type-tag">' + f.type + '</span></div>' +
            '<div class="fc-name">' + f.name + '</div>' +
            '<div class="fc-meta"><span>&#128190; ' + f.size + '</span></div></div>' +
            '<div class="fc-actions pub"><a href="' + f.watch + '" target="_blank" class="btn-play">&#9654; Stream/Play</a></div>' +
            '</div>';
      });
      
      document.getElementById('results').innerHTML=html;
      nextOff=data.next_offset;
      document.getElementById('pageBox').style.display='flex';
      document.getElementById('pBtn').disabled=(off===0);
      document.getElementById('nBtn').disabled=!nextOff;
      document.getElementById('pgInfo').textContent='Page '+curPage;
      
  } catch(e) {
      showToast('Network error','error');
  }
}

function next(){if(nextOff){curPage++;doSearch(nextOff);scrollTo(0,0);}}
function prev(){if(curPage>1){curPage--;doSearch(Math.max(0,curOff-20));scrollTo(0,0);}}

var _tt;
function showToast(msg,type){
  type=type||'success';
  var t=document.getElementById('toast');
  t.textContent=(type==='success'?'\u2713  ':' ')+msg;t.className='toast '+type+' show';
  clearTimeout(_tt);_tt=setTimeout(function(){t.classList.remove('show');},2800);
}

document.addEventListener('DOMContentLoaded',function(){
  if(typeof initThemeBtn === 'function') initThemeBtn();
  var qInput = document.getElementById('q');
  if(qInput) qInput.addEventListener('keydown',function(e){if(e.key==='Enter')doSearch(0);});
});
</script>"""

def topbar_html(active):
    active_dash = 'active' if active == 'dashboard' else ''
    sidebar = SIDEBAR_HTML.replace('{active_dash}', active_dash)
    return f"""
{sidebar}
<div class="topbar">
  <button class="ham-btn" id="hamBtn" onclick="openSidebar()">
    <span class="ham-line"></span><span class="ham-line"></span><span class="ham-line"></span>
  </button>
  <a class="logo" href="/dashboard"><div class="logo-dot"></div>CINEMATIC_BOT</a>
  <div class="topbar-right">
    <button class="theme-btn" id="themeBtn" onclick="toggleTheme()">
      <span class="ti">&#9728;</span><span class="tl">Light</span>
    </button>
  </div>
</div>"""

# ---------------------------------------------
# LOGIN PAGE
# ---------------------------------------------
@admin_routes.get('/admin')
async def login_page(request):
    html = f"""<!DOCTYPE html><html><head><title>Login</title>{SHARED_HEAD}{THEME_JS}</head><body>
<div class="theme-corner">
  <button class="theme-btn" id="themeBtn" onclick="toggleTheme()">
    <span class="ti">&#9728;</span><span class="tl">Light</span>
  </button>
</div>
<div class="login-wrap"><div class="login-box">
  <div class="login-logo"><div class="logo-dot"></div>CINEMATIC_BOT</div>
  <div class="login-card">
    <h2>Admin access</h2>
    <p class="sub">Enter credentials to continue</p>
    <form action="/login" method="post">
      <label>Username</label>
      <input type="text" name="user" placeholder="admin" required autocomplete="off">
      <label>Password</label>
      <input type="password" name="pass" placeholder="••••••••" required>
      <button class="submit-btn" type="submit">Sign in &#8594;</button>
    </form>
  </div>
</div></div>
<script>document.addEventListener('DOMContentLoaded',initThemeBtn);</script>
</body></html>"""
    return safe_html_response(html)

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
    html = f"""<!DOCTYPE html><html><head><title>Login</title>{SHARED_HEAD}{THEME_JS}</head><body>
<div class="theme-corner">
  <button class="theme-btn" id="themeBtn" onclick="toggleTheme()">
    <span class="ti">&#9728;</span><span class="tl">Light</span>
  </button>
</div>
<div class="login-wrap"><div class="login-box">
  <div class="login-logo"><div class="logo-dot"></div>CINEMATIC_BOT</div>
  <div class="login-card">
    <h2>Admin access</h2>
    <p class="sub">Enter credentials to continue</p>
    <div class="err-box">&#10005; &nbsp;Wrong credentials. Try again.</div>
    <form action="/login" method="post">
      <label>Username</label>
      <input type="text" name="user" placeholder="admin" required autocomplete="off">
      <label>Password</label>
      <input type="password" name="pass" placeholder="••••••••" required>
      <button class="submit-btn" type="submit">Sign in &#8594;</button>
    </form>
  </div>
</div></div>
<script>document.addEventListener('DOMContentLoaded',initThemeBtn);</script>
</body></html>"""
    return safe_html_response(html)

# ---------------------------------------------
# DASHBOARD (login required)
# ---------------------------------------------
@admin_routes.get('/dashboard')
async def admin_dashboard(request):
    if not is_logged_in(request): return web.HTTPFound('/admin')
    try:
        stats = await db_count_documents()
    except Exception:
        stats = {}
    try:
        total_u = await user_db.total_users_count()
    except Exception:
        total_u = 0
        
    if isinstance(stats, int):
        stats = {'total': stats, 'primary': stats, 'cloud': 0, 'archive': 0}
        
    p_count = stats.get('primary', 0)
    c_count = stats.get('cloud', 0)
    a_count = stats.get('archive', 0)
    tb = topbar_html('dashboard')
    
    html = f"""<!DOCTYPE html><html><head><title>Dashboard</title>{SHARED_HEAD}{THEME_JS}</head><body>
{tb}
{SIDEBAR_JS}
<div class="search-zone">
  <div class="search-row">
    <div class="filter-tabs">
      <button class="ftab active" data-col="all" onclick="setCol(this)">All</button>
      <button class="ftab" data-col="primary" onclick="setCol(this)">Primary</button>
      <button class="ftab" data-col="cloud" onclick="setCol(this)">Cloud</button>
      <button class="ftab" data-col="archive" onclick="setCol(this)">Archive</button>
    </div>
    <div class="search-wrap">
      <span class="s-icon">&#9906;</span>
      <input class="search-input" id="q" placeholder="Movie name, series, quality&#8230;">
    </div>
    <button class="search-btn" onclick="doSearch(0)">Search</button>
  </div>
</div>
<div class="main">
  <div class="stats-row">
    <div class="scard green"><div class="scard-label">Primary</div><div class="scard-val">{p_count:,}</div><div class="scard-sub">Main collection</div></div>
    <div class="scard blue"><div class="scard-label">Cloud</div><div class="scard-val">{c_count:,}</div><div class="scard-sub">Remote storage</div></div>
    <div class="scard amber"><div class="scard-label">Archive</div><div class="scard-val">{a_count:,}</div><div class="scard-sub">Backup files</div></div>
    <div class="scard red"><div class="scard-label">Users</div><div class="scard-val">{total_u:,}</div><div class="scard-sub">Total registered</div></div>
  </div>
  
  <div class="results-info" id="resInfo">
    <span class="results-count" id="resCount"></span>
    <span class="results-hint">Click Play to stream file</span>
  </div>
  
  <div id="results">
    <div class="empty"><div class="empty-icon">&#9672;</div><p>Type a movie or series name above<br>and press Search</p></div>
  </div>
  
  <div class="pagination" id="pageBox">
    <button class="pg-btn" id="pBtn" onclick="prev()" disabled>&#8592; Previous</button>
    <span class="pg-info" id="pgInfo">Page 1</span>
    <button class="pg-btn" id="nBtn" onclick="next()">Next &#8594;</button>
  </div>
</div>

<div class="toast" id="toast"></div>
{SEARCH_JS}
</body></html>"""
    return safe_html_response(html)

# ---------------------------------------------
# LOGOUT
# ---------------------------------------------
@admin_routes.get('/logout')
async def logout(request):
    session_id = request.cookies.get('admin_session')
    if hasattr(temp, 'ADMIN_SESSIONS') and session_id in temp.ADMIN_SESSIONS:
        del temp.ADMIN_SESSIONS[session_id]
    res = web.HTTPFound('/admin')
    res.del_cookie('admin_session')
    return res
