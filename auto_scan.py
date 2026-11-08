"""
Solana Rug Radar - Auto Scanner v0.2
Watches newly launched Solana tokens and scores each one with rug_radar.py.
Read-only. Put this file in the same folder as rug_radar.py.

Usage:
    python auto_scan.py              # keep scanning every 60 seconds
    python auto_scan.py --once       # scan one batch and stop
"""
import sys
import csv
import time
import datetime
import requests
from rug_radar import score_token, verdict

NEW_TOKENS = "https://api.rugcheck.xyz/v1/stats/new_tokens"
CHECK_EVERY = 60        # seconds between batches
MAX_PER_BATCH = 10      # tokens scored per batch (keeps within API limits)
PAUSE = 2               # seconds between token checks
ALERT_AT = 60           # score at or above this is flagged HIGH RISK
LOG_FILE = "scan_log.csv"

seen = set()


def new_tokens():
    try:
        r = requests.get(NEW_TOKENS, timeout=20)
        r.raise_for_status()
        return r.json() or []
    except Exception as e:
        print(f"! Could not fetch new tokens: {e}")
        return []


def log(row):
    new_file = False
    try:
        open(LOG_FILE).close()
    except FileNotFoundError:
        new_file = True
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["time", "symbol", "mint", "score", "verdict", "top_reason"])
        w.writerow(row)


def scan_batch():
    fresh = [t for t in new_tokens() if t.get("mint") not in seen][:MAX_PER_BATCH]
    if not fresh:
        print("No new tokens this round.")
        return
    flagged = 0
    for t in fresh:
        mint = t["mint"]
        seen.add(mint)
        symbol = t.get("symbol") or "?"
        _, score, reasons, _, _ = score_token(mint)
        top = max(reasons)[1] if reasons else "No red flags"
        mark = "🚨" if score >= ALERT_AT else ("⚠️" if score >= 30 else "✅")
        print(f"{mark} {symbol:<12} {score:>3}/100  {top}")
        print(f"   https://rugcheck.xyz/tokens/{mint}")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log([now, symbol, mint, score, verdict(score), top])
        if score >= ALERT_AT:
            flagged += 1
        time.sleep(PAUSE)
    print(f"\nBatch done: {len(fresh)} scanned, {flagged} high risk. Saved to {LOG_FILE}\n")


def main():
    once = "--once" in sys.argv
    print("Solana Rug Radar auto-scan started. Ctrl+C to stop.\n")
    while True:
        scan_batch()
        if once:
            break
        time.sleep(CHECK_EVERY)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
