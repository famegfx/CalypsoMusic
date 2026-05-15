import os
import asyncio
import logging
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from pytgcalls.exceptions import NoActiveGroupCall, AlreadyJoinedError
import yt_dlp

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("MusicBot")

# ─── Config ───────────────────────────────────────────────────────────────────
API_ID            = int(os.environ["API_ID"])
API_HASH          = os.environ["API_HASH"]
BOT_TOKEN         = os.environ["BOT_TOKEN"]
ASSISTANT_SESSION = os.environ["ASSISTANT_SESSION"]
PORT              = int(os.environ.get("PORT", 8080))   # Render injects PORT

# ─── Clients ──────────────────────────────────────────────────────────────────
bot = Client(
    "MusicBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

assistant = Client(
    "Assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=ASSISTANT_SESSION,
)

call = PyTgCalls(assistant)

# ─── Queue ────────────────────────────────────────────────────────────────────
queues: dict[int, list[dict]] = {}


# ─── YT-DLP ───────────────────────────────────────────────────────────────────
YDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "socket_timeout": 30,
    "retries": 3,
}


def search_yt(query: str) -> dict | None:
    opts = {**YDL_OPTIONS, "default_search": "ytsearch1"}
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            return {"title": info.get("title", "Unknown"), "url": info["url"]}
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            return None


# ─── Playback ─────────────────────────────────────────────────────────────────
async def play_next(chat_id: int):
    if not queues.get(chat_id):
        return
    track = queues[chat_id][0]
    try:
        await call.play(chat_id, MediaStream(track["url"]))
        logger.info(f"[{chat_id}] Playing: {track['title']}")
    except NoActiveGroupCall:
        queues[chat_id].clear()
        logger.warning(f"[{chat_id}] No active group call.")
    except AlreadyJoinedError:
        pass
    except Exception as e:
        logger.error(f"[{chat_id}] play error: {e}")
        queues[chat_id].pop(0)
        await play_next(chat_id)


@call.on_stream_end()
async def stream_ended(_, update):
    chat_id = update.chat_id
    if queues.get(chat_id):
        queues[chat_id].pop(0)
    await play_next(chat_id)


# ─── Bot Commands ─────────────────────────────────────────────────────────────
@bot.on_message(filters.command(["start", "help"]) & filters.group)
async def cmd_start(_, msg: Message):
    await msg.reply(
        "🎵 **Music Bot Commands**\n\n"
        "▶️ `/play <song>` — Play or queue a song\n"
        "⏭️ `/skip` — Skip current track\n"
        "⏹️ `/stop` — Stop & clear queue\n"
        "📋 `/queue` — Show queue\n"
        "⏸️ `/pause` — Pause\n"
        "▶️ `/resume` — Resume"
    )


@bot.on_message(filters.command("play") & filters.group)
async def cmd_play(_, msg: Message):
    chat_id = msg.chat.id
    query = " ".join(msg.command[1:]).strip()
    if not query:
        await msg.reply("❗ Usage: `/play <song name or URL>`")
        return

    status = await msg.reply("🔍 Searching…")
    track = search_yt(query)
    if not track:
        await status.edit("❌ Song not found. Try a different query.")
        return

    track["requester"] = msg.from_user.mention
    queues.setdefault(chat_id, []).append(track)

    if len(queues[chat_id]) == 1:
        await status.edit(f"▶️ **Now playing:** {track['title']}")
        await play_next(chat_id)
    else:
        await status.edit(f"📋 **Queued #{len(queues[chat_id])}:** {track['title']}")


@bot.on_message(filters.command("skip") & filters.group)
async def cmd_skip(_, msg: Message):
    chat_id = msg.chat.id
    if not queues.get(chat_id):
        await msg.reply("❌ Nothing is playing.")
        return
    skipped = queues[chat_id].pop(0)
    await msg.reply(f"⏭️ Skipped: **{skipped['title']}**")
    try:
        await call.stop_stream(chat_id)
    except Exception:
        pass
    await play_next(chat_id)


@bot.on_message(filters.command("stop") & filters.group)
async def cmd_stop(_, msg: Message):
    queues[msg.chat.id] = []
    try:
        await call.leave_group_call(msg.chat.id)
    except Exception:
        pass
    await msg.reply("⏹️ Stopped and queue cleared.")


@bot.on_message(filters.command("queue") & filters.group)
async def cmd_queue(_, msg: Message):
    q = queues.get(msg.chat.id, [])
    if not q:
        await msg.reply("📋 Queue is empty.")
        return
    lines = [f"{'▶️' if i == 0 else f'{i+1}.'} {t['title']} — {t['requester']}"
             for i, t in enumerate(q)]
    await msg.reply("📋 **Queue:**\n" + "\n".join(lines))


@bot.on_message(filters.command("pause") & filters.group)
async def cmd_pause(_, msg: Message):
    try:
        await call.pause_stream(msg.chat.id)
        await msg.reply("⏸️ Paused.")
    except Exception as e:
        await msg.reply(f"❌ {e}")


@bot.on_message(filters.command("resume") & filters.group)
async def cmd_resume(_, msg: Message):
    try:
        await call.resume_stream(msg.chat.id)
        await msg.reply("▶️ Resumed.")
    except Exception as e:
        await msg.reply(f"❌ {e}")


# ─── Web Server (required for Render free Web Service) ────────────────────────
async def health(request):
    return web.Response(text="✅ Music Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Web server listening on port {PORT}")


# ─── Main ─────────────────────────────────────────────────────────────────────
async def main():
    await start_web_server()
    await bot.start()
    await assistant.start()
    await call.start()
    logger.info("✅ Bot is live!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
