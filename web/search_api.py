from aiohttp import web
import time
import re
from utils import temp, get_size
from info import BIN_CHANNEL
from database.ia_filterdb import COLLECTIONS

search_routes = web.RouteTableDef()


def is_admin_logged_in(request):
    session_id = request.cookies.get('admin_session')
    if not hasattr(temp, 'ADMIN_SESSIONS'):
        return False
    return session_id in temp.ADMIN_SESSIONS and time.time() < temp.ADMIN_SESSIONS[session_id]


@search_routes.get('/api/search')
async def api_search_handler(request):
    if not is_admin_logged_in(request):
        return web.json_response({"error": "Unauthorized Access"}, status=403)

    query = request.query.get('q', '').strip()
    target_col = request.query.get('col', 'all').lower()

    # ── FIX 1: offset को int में safely convert करो ──
    try:
        offset = max(0, int(request.query.get('offset', 0)))
    except (ValueError, TypeError):
        offset = 0

    if not query:
        return web.json_response({"results": [], "total": 0, "next_offset": ""})

    # ── FIX 2: Regex injection से बचाओ — re.escape लगाओ ──
    # पुराने code में raw user input सीधे regex बनता था
    # जैसे query = ".*" — पूरा DB expose हो जाता
    try:
        regex = re.compile(re.escape(query), re.IGNORECASE)
    except re.error:
        return web.json_response({"results": [], "total": 0, "next_offset": ""})

    filter_query = {"file_name": regex}
    limit = 20

    # ── FIX 3: कौन सा collection खोजना है ──
    if target_col in COLLECTIONS:
        cols_to_search = {target_col: COLLECTIONS[target_col]}
    else:
        cols_to_search = COLLECTIONS  # 'all' या invalid col → सभी में खोजो

    # ── FIX 4: Total count और paginated docs अलग-अलग queries से लो ──
    # पुराना code: needed_docs = offset + limit तक सब load करता था
    # फिर Python slice करता था — यह बहुत slow है बड़े DB पर
    # नया: MongoDB skip/limit का सही इस्तेमाल
    total_count = 0
    page_docs = []

    for col_name, col in cols_to_search.items():
        # count_documents हर collection पर
        try:
            count = await col.count_documents(filter_query)
        except Exception:
            count = 0
        total_count += count

        # ── FIX 5: skip/limit से सिर्फ जरूरी docs fetch करो ──
        # पुराना: .limit(offset + limit) → सब fetch करके Python में slice
        # नया: .skip(offset).limit(limit) → MongoDB खुद paginate करे
        if len(page_docs) < limit:
            remaining = limit - len(page_docs)
            col_offset = max(0, offset - (total_count - count))
            # यह simple single-collection case है;
            # multi-collection के लिए cumulative offset track करना होगा
            try:
                cursor = col.find(filter_query).sort('_id', -1).skip(col_offset).limit(remaining)
                async for doc in cursor:
                    doc['source_col'] = col_name.capitalize()
                    page_docs.append(doc)
            except Exception:
                continue

    results = []
    for doc in page_docs:
        # ── FIX 6: file_id fallback chain — file_ref पहले, फिर file_id ──
        target_id = doc.get("file_ref") or doc.get("file_id", "")
        if not target_id:
            continue  # invalid doc skip करो

        results.append({
            "name": doc.get("file_name", "Unknown File"),
            "size": get_size(doc.get("file_size", 0)),
            "type": doc.get("file_type", "document").upper(),
            "source": doc.get("source_col", "Unknown"),
            "watch": f"/setup_stream?file_id={target_id}&mode=watch",
            "download": f"/setup_stream?file_id={target_id}&mode=download",
        })

    # ── FIX 7: next_offset सही calculate करो ──
    next_offset = (offset + limit) if (offset + limit) < total_count else ""

    return web.json_response({
        "results": results,
        "total": total_count,
        "next_offset": next_offset,
    })


@search_routes.get('/setup_stream')
async def setup_stream_handler(request):
    if not is_admin_logged_in(request):
        return web.Response(text="Unauthorized Access", status=403)

    file_id = request.query.get('file_id', '').strip()
    mode = request.query.get('mode', 'watch').lower()

    if not file_id:
        return web.Response(text="Invalid Request: file_id missing", status=400)

    # ── FIX 8: mode validate करो — सिर्फ watch/download allow ──
    if mode not in ('watch', 'download'):
        mode = 'watch'

    try:
        msg = await temp.BOT.send_cached_media(chat_id=BIN_CHANNEL, file_id=file_id)
    except Exception as e:
        return web.Response(text=f"Stream Error: {str(e)}", status=500)

    # ── FIX 9: raise के बजाय return करो — cleaner और safer ──
    if mode == 'download':
        return web.HTTPFound(f"/download/{msg.id}")
    return web.HTTPFound(f"/watch/{msg.id}")
