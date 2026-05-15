# 🎵 Telegram Music Bot — Hosted FREE on Render

Play songs in Telegram **Voice Chats** using an **assistant account** (userbot).  
No VPS, no credit card, runs 24/7 on [Render.com](https://render.com) free tier.

---

## ✅ Features

| Command | Description |
|---------|-------------|
| `/play <song / URL>` | Search YouTube & play (or add to queue) |
| `/skip` | Skip current track |
| `/stop` | Stop playback & clear queue |
| `/queue` | Show current queue |
| `/pause` | Pause stream |
| `/resume` | Resume stream |

---

## 🚀 Step-by-Step Setup

### Step 1 — Get Telegram API credentials

1. Go to [my.telegram.org](https://my.telegram.org) → **API development tools**
2. Create an app → copy **API ID** and **API Hash**

---

### Step 2 — Create a Bot

1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` → choose a name and username
3. Copy the **Bot Token**

---

### Step 3 — Create an Assistant Account

The assistant is a **second Telegram account** (can be any number) that physically joins the voice chat.

> 💡 You can use a spare account or create a new one with a virtual number.

1. Log in to that account once on your phone
2. Make sure this account is **added as a member** to your group

---

### Step 4 — Generate the Assistant Session String

Run this **once on your local PC** (Python 3.10+):

```bash
pip install pyrogram TgCrypto
python gen_session.py
```

Enter the API ID, API Hash, and the **assistant's phone number** when prompted.  
Copy the long session string printed at the end — you'll need it in Step 6.

---

### Step 5 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

> ⚠️ Never commit `.env` files or `.session` files.

---

### Step 6 — Deploy on Render (FREE)

1. Go to [render.com](https://render.com) → **New → Background Worker**
2. Connect your GitHub repo
3. Render auto-detects `render.yaml` — click **Apply**
4. Go to **Environment** tab and add these variables:

| Key | Value |
|-----|-------|
| `API_ID` | your Telegram API ID |
| `API_HASH` | your Telegram API Hash |
| `BOT_TOKEN` | your Bot Token from BotFather |
| `ASSISTANT_SESSION` | the long string from Step 4 |

5. Click **Deploy** → wait ~2 minutes → bot is live!

---

### Step 7 — Add the bot to your group

1. Add **both** the bot AND the assistant account to your Telegram group
2. Give them admin rights (or at least "Manage Voice Chats" for the assistant)
3. Start a Voice Chat in the group (tap group name → Start Voice Chat)
4. Send `/play Never Gonna Give You Up` — the assistant joins and music plays! 🎶

---

## 🛠 Troubleshooting

| Problem | Fix |
|---------|-----|
| `NoActiveGroupCall` | Start a Voice Chat in the group first |
| `FloodWait` | Telegram rate-limited the assistant; wait and retry |
| `ASSISTANT_SESSION` invalid | Re-run `gen_session.py` with the correct credentials |
| Bot not responding | Check Render logs; ensure all 4 env vars are set |
| Music cuts off | yt-dlp URL expired; `/stop` then `/play` again |

---

## 📁 Project Structure

```
telegram-music-bot/
├── bot.py           ← Main bot + assistant + voice chat logic
├── gen_session.py   ← One-time session string generator
├── requirements.txt ← Python dependencies
├── render.yaml      ← Render deployment config
└── .gitignore
```

---

## 📝 Notes

- Render free tier **Worker** services run 24/7 (no sleep like web services).
- `yt-dlp` streams audio directly — **no files are saved**, keeping storage at zero.
- The assistant account must stay in the group; kicking it stops music.
