import os, re, time, asyncio, json
from hydrogram import Client, filters, enums
from hydrogram.errors import FloodWait
from hydrogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from info import ADMINS, LOG_CHANNEL
from database.ia_filterdb import save_file
from utils import temp, get_readable_time

# ==========================================
# 🧠 SMART QUEUE & STATE MANAGEMENT
# ==========================================
INDEX_QUEUE = []
IS_INDEXING = False
STATE_FILE = "index_state.json"
RESUME_CHECKED = False

def save_st(data):
    with open(STATE_FILE, "w") as f: json.dump(data, f)

def load_st():
    return json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else None

@Client.on_message(filters.all, group=-99)
async def _resume_hook(c, m):
    global RESUME_CHECKED
    if not RESUME_CHECKED:
        RESUME_CHECKED = True
        task = load_st()
        if task:
            INDEX_QUEUE.insert(0, task)
            asyncio.create_task(process_q(c))

# ==========================================
# ⚙️ QUEUE PROCESSOR (Background Worker)
# ==========================================
async def process_q(bot):
    global IS_INDEXING
    if IS_INDEXING or not INDEX_QUEUE: return
    IS_INDEXING = True
    
    t = INDEX_QUEUE.pop(0)
    save_st(t) 
    
    try: chat_title = (await bot.get_chat(t['chat'])).title
    except: chat_title = "Unknown"
    
    try:
        status_msg = await bot.send_message(t['msg_chat'], f"⏳ **Started Indexing!**\n📢 Channel: `{chat_title}`")
    except: status_msg = None
    
    start_t = time.time()
    tf = dup = err = dlt = no_m = bad = 0
    cur = t['skip']
    
    try:
        async for m in bot.iter_messages(t['chat'], t['lst'], t['skip']):
            if temp.CANCEL:
                temp.CANCEL = False
                break
            
            cur += 1
            if cur % 50 == 0:
                t['skip'] = cur
                save_st(t) # 💾 Auto-Resume Save Point
                try:
                    if status_msg:
                        await status_msg.edit(
                            f"<b>📊 Indexing in Progress...</b>\n\n"
                            f"📢 <b>Channel:</b> {chat_title}\n"
                            f"📨 <b>Processed:</b> {cur} / {t['lst']}\n"
                            f"⏱ <b>Time:</b> {get_readable_time(time.time()-start_t)}",
                            reply_markup=IKM([[IKB('🛑 CANCEL', callback_data='index#cancel')]])
                        )
                except FloodWait as e: await asyncio.sleep(e.value)
                except: pass

            if m.empty: dlt += 1; continue
            if not m.media or m.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.DOCUMENT]: no_m += 1; continue
            
            md = getattr(m, m.media.value, None)
            if not md or getattr(md, 'file_size', 0) < 2097152: bad += 1; continue
            
            md.caption = m.caption
            if getattr(md, 'file_name', None):
                nm, ext = os.path.splitext(md.file_name)
                md.file_name = f"{re.sub(r'@\w+|[_+.-]', ' ', nm).strip()}{ext}"
            
            sts = await save_file(md, collection_type=t['col'])
            if sts == 'suc': tf += 1
            elif sts == 'dup': dup += 1
            elif sts == 'err': err += 1
            
    except Exception as e:
        print(f"Index Error: {e}")
    finally:
        IS_INDEXING = False
        if os.path.exists(STATE_FILE): os.remove(STATE_FILE) 
        
        # 📊 Final Custom Report (As per your Screenshot)
        total_non_media = no_m + bad + dlt # Combining all ignored files into Non-media
        
        report = (
            f"📊 **Index Report**\n\n"
            f"📢 **Channel:** {chat_title}\n"
            f"🆔 **Channel ID:** `{t['chat']}`\n\n"
            f"✅ **Saved:** {tf}\n"
            f"♻️ **Duplicate:** {dup}\n"
            f"❌ **Errors:** {err}\n"
            f"🚫 **Non-media:** {total_non_media}\n"
            f"⏱ **Time:** {get_readable_time(time.time()-start_t)}"
        )
        
        if status_msg: 
            try: await status_msg.edit(report)
            except: pass
            
        try: await bot.send_message(LOG_CHANNEL, report)
        except: pass
        
        # 🔄 Process Next in Queue
        asyncio.create_task(process_q(bot))

# ==========================================
# 🎛 CALLBACKS & INITIATOR 
# ==========================================
@Client.on_callback_query(filters.regex(r'^index'))
async def index_cbs(bot, q):
    d = q.data.split("#")
    idnt = d[1]
    
    if idnt in ['yes', 'ask_skip']:
        chat, lst = d[2], d[3]
        skip = int(d[4]) if idnt == 'yes' else 0
        
        if idnt == 'ask_skip':
            await q.message.edit("📝 **Send messages to skip:** (Send `0` for none)")
            try:
                msg = await bot.listen(chat_id=q.message.chat.id, user_id=q.from_user.id, timeout=60)
                skip = int(msg.text)
                await msg.delete()
            except: return await q.message.edit("❌ Invalid/Timeout.")
            
        b = [[IKB('✅ PRIMARY', callback_data=f'index#start#{chat}#{lst}#{skip}#primary'), IKB('📂 CLOUD', callback_data=f'index#start#{chat}#{lst}#{skip}#cloud')],
             [IKB('📦 ARCHIVES', callback_data=f'index#start#{chat}#{lst}#{skip}#archive')], [IKB('❌ CANCEL', callback_data='close_data')]]
        await q.message.edit(f"🗂️ **Select Collection:**\n⏭️ Skip: `{skip}`", reply_markup=IKM(b))
        
    elif idnt == 'start':
        chat, lst, skip, col = d[2], d[3], int(d[4]), d[5]
        chat = int(chat) if str(chat).lstrip('-').isnumeric() else chat
        
        INDEX_QUEUE.append({'chat': chat, 'lst': int(lst), 'skip': skip, 'col': col, 'msg_chat': q.message.chat.id})
        
        if IS_INDEXING:
            await q.message.edit(f"⏳ **Task Queued!** (Position: `{len(INDEX_QUEUE)}`)\nIt will start automatically when previous is done.")
        else:
            await q.message.edit("🚀 Starting indexing process...")
            asyncio.create_task(process_q(bot))
            
    elif idnt == 'cancel':
        temp.CANCEL = True
        await q.answer("Cancelling current indexing...", show_alert=True)

@Client.on_message(filters.private & filters.user(ADMINS) & (filters.forwarded | filters.text))
async def auto_index(bot, m):
    if m.text and not m.text.startswith("https://t.me"):
        if not m.forward_from_chat: return
        
    if m.forward_from_chat and m.forward_from_chat.type == enums.ChatType.CHANNEL:
        lst, cid = m.forward_from_message_id, m.forward_from_chat.username or m.forward_from_chat.id
    elif m.text and m.text.startswith("https://t.me"):
        try:
            parts = m.text.split("/")
            lst, cid = int(parts[-1]), parts[-2]
            if cid.isnumeric(): cid = int(f"-100{cid}")
        except: return await m.reply('❌ Invalid link!')
    else: return
    
    try: chat = await bot.get_chat(cid)
    except Exception as e: return await m.reply(f'❌ Error: {e}')
    if chat.type != enums.ChatType.CHANNEL: return await m.reply("⚠️ Only channels can be indexed.")
    
    b = [[IKB('⚡ START (Skip 0)', callback_data=f'index#yes#{cid}#{lst}#0')],
         [IKB('📝 CUSTOM SKIP', callback_data=f'index#ask_skip#{cid}#{lst}')], [IKB('❌ CANCEL', callback_data='close_data')]]
    await m.reply(f'🗂️ **Ready to Index:**\n📢 {chat.title}\n📨 Total: `{lst}`', reply_markup=IKM(b))
