"""
Solana Rug Radar - Telegram Alerts v0.4
Scans new Solana tokens and sends a Telegram alert for every HIGH RISK one.
Read-only. Keep in the same folder as rug_radar.py.

Setup (one time):
  1. In Telegram, message @BotFather, send /newbot, copy the bot token.
  2. Send any message to your new bot (or add it to your channel as admin).
  3. Set your token and chat:
       export TELEGRAM_BOT_TOKEN="123456:ABC..."
       export TELEGRAM_CHAT_ID="your_chat_id"     # or "@yourchannel"
     Don't know your chat id? Run:  python telegram_alerts.py --find-chat

Run:
  python telegram_alerts.py            # scan forever, alert on high risk
  python telegram_alerts.py --test     # send one test message
"""
import os
import sys
import time
import requests
from rug_radar import score_token, verdict

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
API = f"https://api.telegram.org/bot{TOKEN}"

NEW_TOKENS = "https://api.rugcheck.xyz/v1/stats/new_tokens"
CHECK_EVERY = 60      # seconds between batches
MAX_PER_BATCH = 10
PAUSE = 2
ALERT_AT = 60         # alert when score is at or above this

seen = set()


def send(text):
    if not TOKEN or not CHAT_ID:
        print("! Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first.")
        return False
    try:
        r = requests.post(f"{API}/sendMessage", timeout=20, data={
            "chat_id": CHAT_ID, "text": text,
            "parse_mode": "HTML", "disable_web_page_preview": True})
        if not r.ok:
            print(f"! Telegram error: {r.text}")
        return r.ok
    except Exception as e:
        print(f"! Could not reach Telegram: {e}")
        return False


def find_chat():
    if not TOKEN:
        print("! Set TELEGRAM_BOT_TOKEN first.")
        return
    updates = requests.get(f"{API}/getUpdates", timeout=20).json().get("result", [])
    if not updates:
        print("No messages yet. Send your bot a message in Telegram, then run this again.")
    for u in updates:
        chat = (u.get("message") or u.get("channel_post") or {}).get("chat", {})
        if chat:
            print(f"Chat id: {chat.get('id')}  ({chat.get('title') or chat.get('username') or chat.get('first_name')})")


def alert_text(symbol, mint, score, reasons):
    lines = [f"🚨 <b>HIGH RISK: {symbol}</b>  {score}/100",
             f"<i>{verdict(score)}</i>", ""]
    for pts, why in sorted(reasons, reverse=True)[:4]:
        lines.append(f"• {why}")
    lines += ["", f"<code>{mint}</code>",
              f'<a href="https://rugcheck.xyz/tokens/{mint}">RugCheck</a> | '
              f'<a href="https://dexscreener.com/solana/{mint}">DexScreener</a>',
              "", "Solana Rug Radar. Not financial advice."]
    return "\n".join(lines)


def scan_batch():
    try:
        tokens = requests.get(NEW_TOKENS, timeout=20).json() or []
    except Exception as e:
        print(f"! Could not fetch new tokens: {e}")
        return
    fresh = [t for t in tokens if t.get("mint") not in seen][:MAX_PER_BATCH]
    for t in fresh:
        mint, symbol = t["mint"], t.get("symbol") or "?"
        seen.add(mint)
        _, score, reasons, _, _ = score_token(mint)
        print(f"{symbol:<12} {score:>3}/100")
        if score >= ALERT_AT:
            if send(alert_text(symbol, mint, score, reasons)):
                print("   -> alert sent")
        time.sleep(PAUSE)


def main():
    if "--find-chat" in sys.argv:
        return find_chat()
    if "--test" in sys.argv:
        ok = send("✅ Solana Rug Radar is connected. High-risk alerts will appear here.")
        return print("Test sent!" if ok else "Test failed.")
    if not TOKEN or not CHAT_ID:
        print("! Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first (see top of file).")
        return
    send("📡 Solana Rug Radar started watching new launches.")
    print("Watching new Solana tokens. Ctrl+C to stop.\n")
    while True:
        scan_batch()
        time.sleep(CHECK_EVERY)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
