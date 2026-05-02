from info import BIN_CHANNEL, URL
from utils import temp
import urllib.parse
import html
import logging

# Logger Setup
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 🎨 FAST FINDER — Premium Streaming Template
# ─────────────────────────────────────────────
watch_tmplt = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{heading}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <style>
        /* ── THEME VARIABLES ── */
        :root {{
            --accent:       #00C2FF;
            --accent-glow:  rgba(0, 194, 255, 0.25);
            --accent-dim:   rgba(0, 194, 255, 0.12);
            --radius:       14px;
            --font-main:    'Sora', sans-serif;
            --font-mono:    'JetBrains Mono', monospace;
            --transition:   0.28s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        [data-theme="dark"] {{
            --bg:           #0a0a0f;
            --bg-card:      #111118;
            --bg-surface:   #1a1a24;
            --bg-hover:     #22222e;
            --border:       rgba(255,255,255,0.07);
            --text-primary: #f0f0ff;
            --text-muted:   #7a7a9a;
            --text-sub:     #4a4a6a;
            --shadow-card:  0 8px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05);
        }}

        [data-theme="light"] {{
            --bg:           #f0f0f8;
            --bg-card:      #ffffff;
            --bg-surface:   #e8e8f4;
            --bg-hover:     #dcdcf0;
            --border:       rgba(0,0,0,0.08);
            --text-primary: #0a0a1a;
            --text-muted:   #5a5a7a;
            --text-sub:     #9a9ab8;
            --shadow-card:  0 8px 40px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.06);
        }}

        /* ── RESET ── */
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

        /* ── BASE ── */
        body {{
            font-family: var(--font-main);
            background-color: var(--bg);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            transition: background-color var(--transition), color var(--transition);
            overflow-x: hidden;
        }}

        /* ── ANIMATED BACKGROUND GRID ── */
        body::before {{
            content: '';
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(rgba(0,194,255,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,194,255,0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            pointer-events: none;
            z-index: 0;
            opacity: 1;
            transition: opacity var(--transition);
        }}
        [data-theme="light"] body::before {{ opacity: 0.4; }}

        /* ── AMBIENT ORBS ── */
        .orb {{
            position: fixed;
            border-radius: 50%;
            filter: blur(120px);
            pointer-events: none;
            z-index: 0;
            opacity: 0.18;
            animation: orb-drift 12s ease-in-out infinite alternate;
        }}
        .orb-1 {{
            width: 500px; height: 500px;
            background: radial-gradient(circle, #00C2FF, transparent 70%);
            top: -200px; right: -100px;
        }}
        .orb-2 {{
            width: 400px; height: 400px;
            background: radial-gradient(circle, #7B61FF, transparent 70%);
            bottom: -150px; left: -100px;
            animation-delay: -6s;
        }}
        @keyframes orb-drift {{
            from {{ transform: translate(0, 0) scale(1); }}
            to   {{ transform: translate(30px, -30px) scale(1.08); }}
        }}
        [data-theme="light"] .orb {{ opacity: 0.08; }}

        /* ── NAVBAR ── */
        .navbar {{
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 200;
            padding: 0 5%;
            height: 64px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            background: rgba(10,10,15,0.7);
            border-bottom: 1px solid var(--border);
            transition: background var(--transition), border-color var(--transition);
        }}
        [data-theme="light"] .navbar {{
            background: rgba(240,240,248,0.75);
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            user-select: none;
        }}
        .logo-svg {{
            height: 36px;
            width: auto;
            display: block;
            filter: drop-shadow(0 0 8px rgba(0,162,229,0.3));
            transition: filter var(--transition);
        }}
        .logo-svg:hover {{
            filter: drop-shadow(0 0 14px rgba(0,162,229,0.5));
        }}

        /* ── THEME TOGGLE ── */
        .theme-toggle {{
            width: 52px; height: 28px;
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 100px;
            cursor: pointer;
            position: relative;
            transition: background var(--transition);
            flex-shrink: 0;
        }}
        .theme-toggle::after {{
            content: '';
            position: absolute;
            top: 3px; left: 3px;
            width: 20px; height: 20px;
            border-radius: 50%;
            background: linear-gradient(135deg, #00C2FF, #7B61FF);
            transition: transform var(--transition);
            box-shadow: 0 2px 8px rgba(0,194,255,0.4);
        }}
        [data-theme="light"] .theme-toggle::after {{
            transform: translateX(24px);
            background: linear-gradient(135deg, #f5a623, #f97316);
            box-shadow: 0 2px 8px rgba(249,115,22,0.4);
        }}
        .theme-icon {{
            position: absolute;
            top: 50%; transform: translateY(-50%);
            font-size: 10px;
            pointer-events: none;
            transition: opacity var(--transition);
        }}
        .theme-icon.moon {{ right: 6px; opacity: 1; }}
        .theme-icon.sun  {{ left: 6px; opacity: 0; }}
        [data-theme="light"] .theme-icon.moon {{ opacity: 0; }}
        [data-theme="light"] .theme-icon.sun  {{ opacity: 1; }}

        /* ── MAIN LAYOUT ── */
        .main {{
            position: relative;
            z-index: 1;
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 88px 5% 60px;
            max-width: 1100px;
            margin: 0 auto;
            width: 100%;
            gap: 28px;
            animation: page-in 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
        }}
        @keyframes page-in {{
            from {{ opacity: 0; transform: translateY(24px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}

        /* ── PLAYER CARD ── */
        .player-card {{
            width: 100%;
            background: var(--bg-card);
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: var(--shadow-card);
            border: 1px solid var(--border);
            position: relative;
            transition: box-shadow var(--transition), background var(--transition);
        }}
        .player-card:hover {{
            box-shadow: var(--shadow-card), 0 0 0 1px rgba(0,194,255,0.15), 0 0 60px rgba(0,194,255,0.08);
        }}

        /* Accent top bar */
        .player-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, #00C2FF, #7B61FF, #00C2FF);
            background-size: 200% 100%;
            animation: shimmer 3s linear infinite;
            z-index: 10;
        }}
        @keyframes shimmer {{
            from {{ background-position: 0% 0%; }}
            to   {{ background-position: 200% 0%; }}
        }}

        /* ── VIDEO WRAPPER ── */
        .video-wrapper {{
            position: relative;
            width: 100%;
            background: #000;
        }}

        .video-wrapper video {{
            width: 100%;
            display: block;
        }}

        /* ── DOUBLE-TAP ZONES ── */
        .tap-zone {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 35%;
            z-index: 5;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .tap-zone.left  {{ left: 0; }}
        .tap-zone.right {{ right: 0; }}

        /* Ripple feedback */
        .tap-ripple {{
            position: absolute;
            width: 80px; height: 80px;
            border-radius: 50%;
            background: rgba(255,255,255,0.15);
            border: 2px solid rgba(255,255,255,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            opacity: 0;
            transform: scale(0.6);
            transition: none;
            pointer-events: none;
            backdrop-filter: blur(4px);
        }}
        .tap-ripple.active {{
            animation: tap-pop 0.65s ease-out forwards;
        }}
        @keyframes tap-pop {{
            0%   {{ opacity: 0; transform: scale(0.6); }}
            20%  {{ opacity: 1; transform: scale(1.1); }}
            60%  {{ opacity: 1; transform: scale(1); }}
            100% {{ opacity: 0; transform: scale(0.9); }}
        }}
        .tap-ripple svg {{
            width: 24px; height: 24px;
            color: white;
        }}
        .tap-ripple span {{
            font-size: 9px;
            font-weight: 700;
            color: white;
            letter-spacing: 0.5px;
            margin-top: 2px;
            font-family: var(--font-mono);
        }}

        /* Chevron arrows */
        .tap-arrows {{
            position: absolute;
            display: flex;
            gap: 3px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.15s;
        }}
        .tap-arrows.visible {{ opacity: 1; }}
        .tap-arrows svg {{
            width: 18px; height: 18px;
            color: rgba(255,255,255,0.7);
        }}

        /* ── PLYR OVERRIDES ── */
        .plyr--video {{
            --plyr-color-main: #00C2FF;
            --plyr-video-background: #000;
            --plyr-font-family: var(--font-main);
            --plyr-font-size-small: 12px;
            --plyr-control-radius: 8px;
        }}
        .plyr__controls {{
            background: linear-gradient(transparent, rgba(0,0,0,0.85)) !important;
            padding: 16px !important;
        }}
        .plyr__control--overlaid {{
            background: rgba(0,194,255,0.85) !important;
            box-shadow: 0 0 0 6px rgba(0,194,255,0.2) !important;
        }}

        /* ── INFO PANEL ── */
        .info-panel {{
            width: 100%;
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 24px 28px;
            box-shadow: var(--shadow-card);
            border: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 20px;
            transition: background var(--transition);
            animation: page-in 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both;
        }}

        .file-meta {{
            display: flex;
            align-items: flex-start;
            gap: 14px;
        }}
        .file-icon-wrap {{
            width: 44px; height: 44px;
            border-radius: 10px;
            background: var(--accent-dim);
            border: 1px solid rgba(0,194,255,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .file-icon-wrap svg {{
            width: 20px; height: 20px;
            color: var(--accent);
        }}
        .file-title {{
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.3;
            word-break: break-word;
        }}
        .file-badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            margin-top: 6px;
            padding: 3px 10px;
            background: var(--accent-dim);
            border: 1px solid rgba(0,194,255,0.2);
            border-radius: 100px;
            font-size: 0.7rem;
            font-weight: 600;
            color: var(--accent);
            font-family: var(--font-mono);
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}

        /* ── DIVIDER ── */
        .divider {{
            height: 1px;
            background: var(--border);
        }}

        /* ── ACTION BUTTONS ── */
        .actions {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px 22px;
            font-family: var(--font-main);
            font-size: 0.88rem;
            font-weight: 600;
            border-radius: 10px;
            cursor: pointer;
            border: none;
            text-decoration: none;
            transition: transform 0.18s, box-shadow 0.18s, background 0.18s, opacity 0.18s;
            letter-spacing: 0.2px;
            white-space: nowrap;
        }}
        .btn:active {{ transform: scale(0.96) !important; }}

        .btn-primary {{
            background: linear-gradient(135deg, #00C2FF, #7B61FF);
            color: #fff;
            box-shadow: 0 4px 20px rgba(0,194,255,0.3);
        }}
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 28px rgba(0,194,255,0.45);
        }}

        .btn-ghost {{
            background: var(--bg-surface);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }}
        .btn-ghost:hover {{
            background: var(--bg-hover);
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}

        .btn svg {{ width: 16px; height: 16px; flex-shrink: 0; }}

        /* ── SKIP TIP ── */
        .skip-tip {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            background: var(--bg-surface);
            border-radius: 8px;
            border: 1px solid var(--border);
            font-size: 0.78rem;
            color: var(--text-muted);
        }}
        .skip-tip svg {{ width: 14px; height: 14px; color: var(--accent); flex-shrink: 0; }}

        /* ── TOAST ── */
        #toast {{
            position: fixed;
            bottom: 28px; right: 28px;
            z-index: 999;
            padding: 14px 20px;
            background: var(--bg-card);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-left: 3px solid var(--accent);
            border-radius: 10px;
            font-size: 0.88rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            transform: translateY(80px);
            opacity: 0;
            transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.35s;
            pointer-events: none;
        }}
        #toast.show {{
            transform: translateY(0);
            opacity: 1;
        }}
        #toast svg {{ width: 16px; height: 16px; color: var(--accent); }}

        /* ── FOOTER ── */
        footer {{
            position: relative;
            z-index: 1;
            text-align: center;
            padding: 24px;
            font-size: 0.75rem;
            color: var(--text-sub);
            border-top: 1px solid var(--border);
        }}
        footer span {{
            color: var(--accent);
            font-weight: 600;
        }}

        /* ── RESPONSIVE ── */
        @media (max-width: 640px) {{
            .navbar {{ padding: 0 4%; }}
            .main {{ padding: 80px 4% 48px; gap: 16px; }}
            .info-panel {{ padding: 18px; gap: 16px; }}
            .file-title {{ font-size: 1rem; }}
            .btn {{ flex: 1; font-size: 0.82rem; padding: 12px 16px; }}
            .logo-text {{ display: none; }}
            #toast {{ right: 16px; bottom: 16px; left: 16px; }}
        }}
    </style>
</head>
<body>

    <!-- Ambient Orbs -->
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>

    <!-- Navbar -->
    <nav class="navbar">
        <a class="logo" href="/">
            <svg class="logo-svg" viewBox="0 0 260 80" xmlns="http://www.w3.org/2000/svg">
                <!-- Speed lines -->
                <line x1="2"  y1="18" x2="32" y2="18" stroke="#00A2E5" stroke-width="5" stroke-linecap="round"/>
                <line x1="8"  y1="28" x2="34" y2="28" stroke="#00A2E5" stroke-width="5" stroke-linecap="round"/>
                <line x1="14" y1="38" x2="36" y2="38" stroke="#00A2E5" stroke-width="5" stroke-linecap="round"/>
                <line x1="8"  y1="48" x2="34" y2="48" stroke="#00A2E5" stroke-width="5" stroke-linecap="round"/>
                <line x1="2"  y1="58" x2="32" y2="58" stroke="#00A2E5" stroke-width="5" stroke-linecap="round"/>
                <!-- Magnifier circle -->
                <circle cx="68" cy="30" r="18" fill="none" stroke="#00A2E5" stroke-width="6"/>
                <!-- Magnifier handle -->
                <line x1="80" y1="42" x2="95" y2="60" stroke="#00A2E5" stroke-width="6" stroke-linecap="round"/>
                <!-- Lens shine -->
                <path d="M60 22 Q65 18 72 20" stroke="white" stroke-width="2.5" stroke-linecap="round" fill="none" opacity="0.6"/>
                <!-- FAST text -->
                <text x="108" y="58" font-family="'Sora','Arial Black',sans-serif" font-weight="900" font-size="34" fill="#F26522" letter-spacing="-0.5">FAST</text>
                <!-- FINDER text -->
                <text x="172" y="58" font-family="'Sora','Arial Black',sans-serif" font-weight="900" font-size="34" fill="#00A2E5" letter-spacing="-0.5">FINDER</text>
            </svg>
        </a>

        <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">
            <span class="theme-icon moon">🌙</span>
            <span class="theme-icon sun">☀️</span>
        </button>
    </nav>

    <!-- Main Content -->
    <main class="main">

        <!-- Player Card -->
        <div class="player-card">
            <div class="video-wrapper">
                <video id="player" playsinline>
                    <source src="{src}" type="{mime_type}" />
                </video>

                <!-- Double-tap zones -->
                <div class="tap-zone left" id="tapLeft">
                    <div class="tap-ripple" id="rippleLeft">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M11 19l-7-7 7-7M18 19l-7-7 7-7"/>
                        </svg>
                        <span>-5s</span>
                    </div>
                </div>
                <div class="tap-zone right" id="tapRight">
                    <div class="tap-ripple" id="rippleRight">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M13 5l7 7-7 7M6 5l7 7-7 7"/>
                        </svg>
                        <span>+5s</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Info Panel -->
        <div class="info-panel">
            <div class="file-meta">
                <div class="file-icon-wrap">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="23 7 16 12 23 17 23 7"/>
                        <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                    </svg>
                </div>
                <div>
                    <div class="file-title">{file_name}</div>
                    <div class="file-badge">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:10px;height:10px;">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M10 8l6 4-6 4V8z"/>
                        </svg>
                        {mime_type}
                    </div>
                </div>
            </div>

            <div class="divider"></div>

            <div class="actions">
                <a href="{src}" download class="btn btn-primary">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                    Download
                </a>

                <button onclick="copyLink()" class="btn btn-ghost">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                    Copy Link
                </button>
            </div>

            <div class="skip-tip">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <span>Tip: Double-tap the left side to rewind 5s, right side to skip forward 5s</span>
            </div>
        </div>

    </main>

    <footer>
        Powered by <span style="color:#F26522;">FAST</span><span>FINDER</span> — Fast. Private. Yours.
    </footer>

    <!-- Toast Notification -->
    <div id="toast">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
        </svg>
        Link copied to clipboard!
    </div>

    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script>
        // ── PLYR INIT ──
        const player = new Plyr('#player', {{
            controls: [
                'play-large', 'play', 'rewind', 'fast-forward',
                'progress', 'current-time', 'duration',
                'mute', 'volume', 'settings',
                'pip', 'airplay', 'fullscreen'
            ],
            settings: ['captions', 'quality', 'speed'],
            seekTime: 5,
            keyboard: {{ focused: true, global: true }},
            tooltips: {{ controls: true, seek: true }},
            hideControls: true,
            clickToPlay: false,  // We handle center click manually
        }});

        // ── THEME ──
        function toggleTheme() {{
            const html = document.documentElement;
            html.dataset.theme = html.dataset.theme === 'dark' ? 'light' : 'dark';
            localStorage.setItem('ff-theme', html.dataset.theme);
        }}
        // Restore saved theme
        (function() {{
            const saved = localStorage.getItem('ff-theme');
            if (saved) document.documentElement.dataset.theme = saved;
        }})();

        // ── DOUBLE-TAP SKIP (YouTube style) ──
        let tapTimer = null;
        let tapCount = 0;

        function showRipple(side) {{
            const ripple = document.getElementById('ripple' + (side === 'left' ? 'Left' : 'Right'));
            ripple.classList.remove('active');
            void ripple.offsetWidth; // reflow
            ripple.classList.add('active');
            setTimeout(() => ripple.classList.remove('active'), 700);
        }}

        function handleTap(side, e) {{
            // Prevent affecting plyr's center
            e.stopPropagation();
            tapCount++;

            if (tapCount === 2) {{
                const vid = document.querySelector('video');
                if (!vid) return;
                if (side === 'left') {{
                    vid.currentTime = Math.max(0, vid.currentTime - 5);
                }} else {{
                    vid.currentTime = Math.min(vid.duration || Infinity, vid.currentTime + 5);
                }}
                showRipple(side);
                tapCount = 0;
                clearTimeout(tapTimer);
            }} else {{
                tapTimer = setTimeout(() => {{
                    // Single tap = toggle play/pause
                    if (tapCount === 1) player.togglePlay();
                    tapCount = 0;
                }}, 250);
            }}
        }}

        document.getElementById('tapLeft').addEventListener('click',  (e) => handleTap('left', e));
        document.getElementById('tapRight').addEventListener('click', (e) => handleTap('right', e));

        // ── COPY LINK ──
        function copyLink() {{
            const url = "{src}";
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(url).then(showToast);
            }} else {{
                const el = document.createElement('textarea');
                el.value = url;
                el.style.position = 'fixed';
                el.style.opacity = '0';
                document.body.appendChild(el);
                el.select();
                document.execCommand('copy');
                document.body.removeChild(el);
                showToast();
            }}
        }}

        function showToast() {{
            const t = document.getElementById('toast');
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3000);
        }}

        // ── KEYBOARD SHORTCUTS ──
        document.addEventListener('keydown', (e) => {{
            if (e.target.tagName === 'INPUT') return;
            const vid = document.querySelector('video');
            if (!vid) return;
            if (e.key === 'ArrowLeft')  {{ vid.currentTime = Math.max(0, vid.currentTime - 5); }}
            if (e.key === 'ArrowRight') {{ vid.currentTime = Math.min(vid.duration, vid.currentTime + 5); }}
        }});
    </script>
</body>
</html>
"""


async def media_watch(message_id):
    try:
        media_msg = await temp.BOT.get_messages(BIN_CHANNEL, message_id)
        media = getattr(media_msg, media_msg.media.value, None)

        if not media:
            return """
            <body style="background:#0a0a0f;color:#f0f0ff;display:flex;align-items:center;
                         justify-content:center;height:100vh;font-family:sans-serif;flex-direction:column;gap:16px;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#00C2FF"
                     stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/>
                    <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
                <h2 style="font-size:1.2rem;font-weight:700;">File not found or deleted</h2>
                <p style="color:#7a7a9a;font-size:0.9rem;">This media may have been removed.</p>
            </body>
            """

        src = urllib.parse.urljoin(URL, f'download/{message_id}')
        mime_type = getattr(media, 'mime_type', 'video/mp4')
        tag = mime_type.split('/')[0].strip()

        if tag == 'video':
            file_name = html.escape(
                getattr(media, 'file_name', None) or "Untitled Video"
            )
            return watch_tmplt.format(
                heading=f"{file_name} — FastFinder",
                file_name=file_name,
                src=src,
                mime_type=mime_type
            )
        else:
            return f"""
            <body style="background:#0a0a0f;color:#f0f0ff;display:flex;align-items:center;
                         justify-content:center;height:100vh;font-family:sans-serif;flex-direction:column;gap:20px;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#00C2FF"
                     stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                <h2 style="font-size:1.2rem;font-weight:700;">Format not supported for streaming</h2>
                <p style="color:#7a7a9a;font-size:0.9rem;">You can still download the file directly.</p>
                <a href="{src}" style="display:inline-flex;align-items:center;gap:8px;padding:12px 24px;
                    background:linear-gradient(135deg,#00C2FF,#7B61FF);color:white;text-decoration:none;
                    border-radius:10px;font-weight:600;font-size:0.9rem;
                    box-shadow:0 4px 20px rgba(0,194,255,0.3);">
                    Download File
                </a>
            </body>
            """

    except Exception as e:
        logger.error(f"Template Error: {e}")
        return f"""
        <body style="background:#0a0a0f;color:#f0f0ff;display:flex;align-items:center;
                     justify-content:center;height:100vh;font-family:sans-serif;">
            <div style="text-align:center;">
                <h2 style="color:#ff4f4f;margin-bottom:10px;">Server Error</h2>
                <p style="color:#7a7a9a;font-size:0.85rem;">{html.escape(str(e))}</p>
            </div>
        </body>
        """
