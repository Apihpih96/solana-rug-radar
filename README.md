# 🚨 Solana Rug Radar

An AI agent that scans newly launched Solana tokens and scores each one **0 to 100 for rug risk**, then explains why in plain words. High-risk tokens are posted live to Telegram.

Built in public for the **Trends Build in Public Hackathon**.

📡 Live alerts: [t.me/SolanaRugRadar](https://t.me/SolanaRugRadar)

## What it checks

| Check | Why it matters | Points |
|---|---|---|
| Mint authority still active | Dev can print unlimited new tokens | +25 |
| Freeze authority still active | Dev can freeze your tokens so you can't sell | +25 |
| Top 10 wallets hold >50% (>30%) | A few whales can dump on everyone | +20 (+10) |
| Insider wallets flagged | Coordinated insiders | +10 |
| Liquidity < $10k (< $50k) | Easy to drain, hard to sell | +15 (+7) |
| Token < 24 hours old | Brand-new launches are riskiest | +10 |
| Already marked rugged | — | +100 |

Pools, lockers and pump.fun bonding curves are excluded from holder concentration, so they don't trigger false whale alerts.

**Score:** 0–29 lower risk · 30–59 caution · 60+ high risk

## Quick start

```bash
pip install -r requirements.txt

# Check one token
python rug_radar.py <TOKEN_MINT_ADDRESS>

# Auto-scan new launches (logs to scan_log.csv)
python auto_scan.py

# Telegram alerts
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="@SolanaRugRadar"
python telegram_alerts.py --test
python telegram_alerts.py
```

## Files

- `rug_radar.py` – scores a single token
- `auto_scan.py` – watches new launches and logs scores
- `telegram_alerts.py` – sends high-risk alerts to Telegram

## Data sources

- [RugCheck](https://rugcheck.xyz) API – token report and new-token feed
- [DexScreener](https://dexscreener.com) API – liquidity and pair age

Read-only: no wallet connection, no private keys.

## Disclaimer

Not financial advice. A low score is not a guarantee. Always DYOR.
