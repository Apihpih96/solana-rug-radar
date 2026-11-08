"""
Solana Rug Radar - v0.3
Checks a Solana token and gives it a simple 0-100 risk score (higher = riskier).
Read-only: uses public RugCheck and DexScreener APIs. No wallet, no keys.

Usage:
    pip install requests
    python rug_radar.py <TOKEN_MINT_ADDRESS>
"""
import sys
import time
import requests

RUGCHECK = "https://api.rugcheck.xyz/v1/tokens/{}/report"
DEXSCREENER = "https://api.dexscreener.com/latest/dex/tokens/{}"


def get_json(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ! Could not reach {url.split('/')[2]}: {e}")
        return None


def score_token(mint):
    rc = get_json(RUGCHECK.format(mint)) or {}
    dx = get_json(DEXSCREENER.format(mint)) or {}

    reasons = []  # (points, plain-English reason)

    # 1. Mint authority: dev can print unlimited new tokens
    if rc.get("mintAuthority"):
        reasons.append((25, "Dev can still mint new tokens (supply not fixed)"))

    # 2. Freeze authority: dev can freeze your tokens so you can't sell
    if rc.get("freezeAuthority"):
        reasons.append((25, "Dev can freeze holders' tokens"))

    # 3. Holder concentration: top 10 holders own too much
    # Skip pools, bonding curves and lockers (e.g. pump.fun curve) - they are not whales
    known = rc.get("knownAccounts") or {}
    skip = {a for a, info in known.items() if (info or {}).get("type") in ("AMM", "LOCKER")}
    for m in rc.get("markets") or []:
        skip.update(filter(None, [m.get("pubkey"), m.get("liquidityA"), m.get("liquidityB")]))
        for side in ("liquidityAAccount", "liquidityBAccount"):
            acct = m.get(side)
            if isinstance(acct, dict) and acct.get("owner"):
                skip.add(acct["owner"])
    holders = [h for h in (rc.get("topHolders") or [])
               if h.get("owner") not in skip and h.get("address") not in skip]
    top10 = sum(h.get("pct", 0) for h in holders[:10])
    if top10 > 50:
        reasons.append((20, f"Top 10 wallets hold {top10:.0f}% of supply"))
    elif top10 > 30:
        reasons.append((10, f"Top 10 wallets hold {top10:.0f}% of supply"))

    # 4. Insiders flagged by RugCheck
    insiders = [h for h in holders if h.get("insider")]
    if insiders:
        reasons.append((10, f"{len(insiders)} top holder(s) flagged as insiders"))

    # 5. Liquidity: low liquidity = easy to drain / hard to sell
    pairs = dx.get("pairs") or []
    liquidity = sum((p.get("liquidity") or {}).get("usd", 0) or 0 for p in pairs)
    if not liquidity:  # brand-new pump.fun tokens are not on DexScreener yet
        liquidity = rc.get("totalMarketLiquidity") or 0
    if liquidity < 10_000:
        reasons.append((15, f"Very low liquidity (${liquidity:,.0f})"))
    elif liquidity < 50_000:
        reasons.append((7, f"Low liquidity (${liquidity:,.0f})"))

    # 6. Token age: brand-new tokens are riskier
    created = min((p.get("pairCreatedAt") or 0 for p in pairs), default=0)
    if created:
        age_hours = (time.time() * 1000 - created) / 3_600_000
        if age_hours < 24:
            reasons.append((10, f"Token is only {age_hours:.0f} hours old"))

    # 7. RugCheck already marked it rugged
    if rc.get("rugged"):
        reasons.append((100, "RugCheck marks this token as RUGGED"))

    score = min(100, sum(p for p, _ in reasons))
    name = (pairs[0]["baseToken"]["name"] if pairs else
            (rc.get("tokenMeta") or {}).get("name", "Unknown"))
    return name, score, reasons, liquidity, top10


def verdict(score):
    if score >= 60:
        return "HIGH RISK - avoid"
    if score >= 30:
        return "CAUTION - do your research"
    return "LOWER RISK - no major red flags"


def main():
    if len(sys.argv) != 2:
        print("Usage: python rug_radar.py <TOKEN_MINT_ADDRESS>")
        sys.exit(1)
    mint = sys.argv[1].strip()
    print(f"\nScanning {mint} ...\n")
    name, score, reasons, liq, top10 = score_token(mint)

    print(f"Token:      {name}")
    print(f"Risk score: {score}/100  ->  {verdict(score)}")
    print(f"Liquidity:  ${liq:,.0f}   |   Top 10 holders: {top10:.0f}%\n")
    if reasons:
        print("Why:")
        for pts, why in sorted(reasons, reverse=True):
            print(f"  +{pts:<3} {why}")
    else:
        print("No red flags found.")
    print("\nNot financial advice. Always do your own research.\n")


if __name__ == "__main__":
    main()
