import logging, re, base64, asyncio
from struct import pack
from motor.motor_asyncio import AsyncIOMotorClient
from hydrogram.file_id import FileId
from info import DATABASE_URL, DATABASE_NAME, MAX_BTN, USE_CAPTION_FILTER

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# ⚙️ DB SETUP & COLLECTIONS (Optimized)
# ─────────────────────────────────────────────────────────
db = AsyncIOMotorClient(
    DATABASE_URL, maxPoolSize=5, minPoolSize=1, serverSelectionTimeoutMS=5000, 
    connectTimeoutMS=10000, socketTimeoutMS=20000, retryWrites=True, retryReads=True
)[DATABASE_NAME]

COLLECTIONS = {"primary": db.Primary, "cloud": db.Cloud, "archive": db.Archive}
COLS = COLLECTIONS  

async def ensure_indexes():
    for n, c in COLS.items():
        try: await c.create_index([("file_name", "text"), ("caption", "text")], name=f"{n}_text")
        except Exception as e:
            if not any(x in str(e) for x in ["already exists", "IndexKeySpecsConflict", "86"]):
                logger.warning(f"Idx err [{n}]: {e}")

async def db_count_documents():
    try:
        p, c, a = await asyncio.gather(*(COLS[k].estimated_document_count() for k in ["primary", "cloud", "archive"]))
        return {"primary": p, "cloud": c, "archive": a, "total": p + c + a}
    except: return {"primary": 0, "cloud": 0, "archive": 0, "total": 0}

# ─────────────────────────────────────────────────────────
# 💾 SAVE & UTILS
# ─────────────────────────────────────────────────────────
# ✅ FIX: Changed col_type back to collection_type
async def save_file(media, collection_type="primary"):
    try:
        fid = unpack_new_file_id(media.file_id)
        if not fid: return "err"
        
        clean = lambda s: re.sub(r"@\w+|[_+.-]", " ", str(s or "")).strip()
        doc = {
            "_id": fid, "file_ref": media.file_id, "file_name": clean(media.file_name), 
            "file_size": media.file_size, "caption": clean(media.caption), "file_type": type(media).__name__.lower()
        }
        res = await COLS.get(collection_type, COLS["primary"]).replace_one({"_id": fid}, doc, upsert=True)
        return "dup" if res.matched_count > 0 else "suc"
    except Exception as e:
        logger.error(f"save_file err: {e}"); return "err"

def _build_regex(q: str):
    q = q.strip()
    raw = r'.' if not q else (r'(\b|[\.\+\-_])' + re.escape(q) + r'(\b|[\.\+\-_])' if ' ' not in q else re.escape(q).replace(r'\ ', r'.*[\s\.\+\-_]'))
    try: return re.compile(raw, re.IGNORECASE)
    except: return re.compile(re.escape(q), re.IGNORECASE)

# ─────────────────────────────────────────────────────────
# 🚀 SMART HYBRID SEARCH
# ─────────────────────────────────────────────────────────
async def _search(col, q: str, regex, off: int, lim: int, lang=None):
    sq = " ".join(f'"{w}"' for w in q.replace('"', '').replace("'", "").split())
    t_flt = {"$text": {"$search": sq}}
    if lang: t_flt = {"$and": [t_flt, {"file_name": re.compile(lang, re.IGNORECASE)}]}
    
    cnt = await col.count_documents(t_flt)
    if cnt > 0:
        docs = await col.find(t_flt, {"score": {"$meta": "textScore"}}).sort([("score", {"$meta": "textScore"})]).skip(off).limit(lim).to_list(lim)
        for d in docs: d["file_id"] = d["_id"]
        return docs, cnt

    r_flt = {"$or": [{"file_name": regex}, {"caption": regex}]} if USE_CAPTION_FILTER else {"file_name": regex}
    if lang: r_flt = {"$and": [r_flt, {"file_name": re.compile(lang, re.IGNORECASE)}]}
    
    cnt = await col.count_documents(r_flt)
    docs = await col.find(r_flt).sort('_id', -1).skip(off).limit(lim).to_list(lim)
    for d in docs: d["file_id"] = d["_id"]
    return docs, cnt

# ✅ FIX: Changed col_type back to collection_type
async def get_search_results(q, lim=MAX_BTN, off=0, lang=None, collection_type="primary"):
    if not q: return [], "", 0, collection_type
    rq, reg = str(q).strip(), _build_regex(str(q).strip())
    
    targets = [("primary", COLS["primary"]), ("cloud", COLS["cloud"]), ("archive", COLS["archive"])] if collection_type == "all" else [(collection_type, COLS.get(collection_type, COLS["primary"]))]
    
    for name, col in targets:
        docs, cnt = await _search(col, rq, reg, off, lim, lang)
        if docs or name == targets[-1][0]: 
            nxt = off + lim if off + lim < cnt else ""
            return docs, nxt, cnt, name

async def get_web_search_results(q, off=0, lim=20):
    if not q: return []
    rq = str(q).strip()
    sq = " ".join(f'"{w}"' for w in rq.replace('"', '').replace("'", "").split())
    reg, t_flt, r_flt = _build_regex(rq), {"$text": {"$search": sq}}, {"file_name": _build_regex(rq)}
    
    res = []
    for col in COLS.values():
        cur = col.find(t_flt, {"score": {"$meta": "textScore"}}).sort([("score", {"$meta": "textScore"})]) if await col.count_documents(t_flt) > 0 else col.find(r_flt).sort('_id', -1)
        docs = await cur.skip(off).limit(lim).to_list(lim)
        for d in docs: 
            d["file_id"] = d["_id"]
            res.append(d)
        if len(res) >= lim: break
    return res[:lim]

# ─────────────────────────────────────────────────────────
# 🗑 DELETE & DETAILS
# ─────────────────────────────────────────────────────────
# ✅ FIX: Changed col_type back to collection_type
async def delete_files(q, collection_type="all"):
    cols = COLS.values() if collection_type == "all" else [COLS.get(collection_type, COLS["primary"])]
    try:
        flt = {} if q == "*" else {"file_name": _build_regex(str(q))}
        return sum((r.deleted_count for r in await asyncio.gather(*(c.delete_many(flt) for c in cols))))
    except Exception as e:
        logger.error(f"del err: {e}"); return 0

async def get_file_details(fid):
    for col in COLS.values():
        if (doc := await col.find_one({"_id": fid})):
            doc["file_id"] = doc["_id"]; return doc
    return None

# ─────────────────────────────────────────────────────────
# 🔑 ENCODING UTILS
# ─────────────────────────────────────────────────────────
def encode_file_id(s: bytes) -> str:
    r, n = b"", 0
    for i in s + b"\x16\x04":
        if i == 0: n += 1
        else:
            if n: r += b"\x00" + bytes([n]); n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def unpack_new_file_id(new_id: str):
    try:
        d = FileId.decode(new_id)
        return encode_file_id(pack("<iiqq", int(d.file_type), d.dc_id, d.media_id, d.access_hash))
    except: return None
