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

    try:
        offset = max(0, int(request.query.get('offset', 0)))
    except (ValueError, TypeError):
        offset = 0

    if not query:
        return web.json_response({"results": [], "total": 0, "next_offset": ""})

    # re.escape se regex injection band
    try:
        regex = re.compile(re.escape(query), re.IGNORECASE)
    except re.error:
        return web.json_response({"results": [], "total": 0, "next_offset": ""})

    filter_query = {"file_name": regex}
    limit = 20

    if target_col in COLLECTIONS:
        cols_to_search = {target_col: COLLECTIONS[target_col]}
    else:
        cols_to_search = COLLECTIONS

    total_count = 0
    all_matches = []

    for col_name, col in cols_to_search.items():
        try:
            count = await col.count_documents(filter_query)
        except Exception:
            count = 0
        total_count += count

        if len(all_matches) < (offset + limit):
            try:
                cursor = col.find(filter_query).sort('_id', -1).limit(offset + limit)
                async for doc in cursor:
                    doc['source_col'] = col_name.lower()
                    all_matches.append(doc)
            except Exception:
                continue

    page_docs = all_matches[offset: offset + limit]

    results = []
    for doc in page_docs:
        raw_id = doc.get("_id", "")
        target_id = doc.get("file_ref") or doc.get("file_id", "")
        if not target_id:
            continue

        results.append({
            "id": str(raw_id),
            "name": doc.get("file_name", "Unknown File"),
            "size": get_size(doc.get("file_size", 0)),
            "type": doc.get("file_type", "document").upper(),
            "source": doc.get("source_col", "primary"),
            "watch": f"/setup_stream?file_id={target_id}&mode=watch",
            "download": f"/setup_stream?file_id={target_id}&mode=download",
        })

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

    if mode not in ('watch', 'download'):
        mode = 'watch'

    try:
        msg = await temp.BOT.send_cached_media(chat_id=BIN_CHANNEL, file_id=file_id)
    except Exception as e:
        return web.Response(text=f"Stream Error: {str(e)}", status=500)

    if mode == 'download':
        return web.HTTPFound(f"/download/{msg.id}")
    return web.HTTPFound(f"/watch/{msg.id}")
