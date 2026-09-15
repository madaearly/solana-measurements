#!/usr/bin/env python3
"""
Find every pool that prices some other token in xSOL, then pull the series needed to
measure what being priced in xSOL costs.

Two different kinds of evidence come out of this and they have different strengths.
Pool creation dates come from the pool endpoint and are exact. Prices come from daily
closes and have to be tested before use (see analyze.py, and METHOD.md rule 5).
"""
import json, time, urllib.request, urllib.parse, datetime as dt

DS = {"User-Agent": "mada/0.1"}
GT = {"Accept": "application/json;version=20230302", "User-Agent": "mada/0.1"}
XSOL = "4sWNB8zGWHkh6UnmwiEtzNxL4XrN7uK9tosbESbJFfVs"
PERP_POOL = "BMQSjcaDs6duyczC4ijZNtjm2ZKe33JwuUdSFYnS2Jww"
PERP_MINT = "2yALLYqGdczwW1JGPsFqvhCfRaHb3jucpjwNSLFznqHM"


def get(url, headers):
    r = urllib.request.Request(url, headers=headers)
    for a in range(5):
        try:
            with urllib.request.urlopen(r, timeout=45) as f:
                return json.load(f)
        except Exception as e:
            if a == 4: return {"err": repr(e)[:70]}
            time.sleep(7 * (a + 1))
    return {}


def quoted_pools():
    """every pool where xSOL is the QUOTE side -- i.e. somebody else's token priced in it"""
    d = get(f"https://api.dexscreener.com/latest/dex/tokens/{XSOL}", DS)
    out = []
    for p in (d.get("pairs") or []):
        if (p.get("quoteToken") or {}).get("address") != XSOL:
            continue
        pa = p.get("pairAddress")
        meta = get(f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pa}", GT)
        a = (meta.get("data") or {}).get("attributes", {})
        out.append({"ticker": (p.get("baseToken") or {}).get("symbol"),
                    "pool": pa, "dex": p.get("dexId"),
                    "created": str(a.get("pool_created_at"))[:10],
                    "liquidity_usd": (p.get("liquidity") or {}).get("usd") or 0,
                    "volume_24h_usd": (p.get("volume") or {}).get("h24") or 0})
        print(f"  {out[-1]['ticker']:<12} opened {out[-1]['created']}  "
              f"${out[-1]['liquidity_usd']:>10,.0f}", flush=True)
        time.sleep(2.5)
    out.sort(key=lambda x: x["created"])
    return out


def ohlcv(pool, label, token=None, pages=3):
    bars, before = {}, None
    for _ in range(pages):
        q = {"aggregate": 1, "limit": 1000}
        if token:  q["token"] = token
        if before: q["before_timestamp"] = before
        d = get("https://api.geckoterminal.com/api/v2/networks/solana/pools/"
                f"{pool}/ohlcv/day?" + urllib.parse.urlencode(q), GT)
        rows = (d.get("data") or {}).get("attributes", {}).get("ohlcv_list")
        if not rows: break
        for b in rows:
            if b[4]: bars[int(b[0])] = float(b[4])
        old = min(int(b[0]) for b in rows)
        if before is not None and old >= before: break
        before = old
        time.sleep(3)
    ks = sorted(bars)
    print(f"  {label:<14} {len(bars):>4} days  "
          f"{dt.datetime.utcfromtimestamp(ks[0]):%Y-%m-%d} -> "
          f"{dt.datetime.utcfromtimestamp(ks[-1]):%Y-%m-%d}" if ks else f"  {label}: empty")
    return bars


if __name__ == "__main__":
    print("pools that price another token in xSOL:")
    pools = quoted_pools()
    json.dump({"captured_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
               "quote_asset": "xSOL", "xsol_mint": XSOL, "pools": pools},
              open("data/xsol_quoted_pools.json", "w"), indent=1)
    print("\nseries:")
    s = {"perp": ohlcv(PERP_POOL, "PERP (USD)", token=PERP_MINT),
         "xsol": ohlcv("coj59LYbLc6DhMwnxxfPc9mUiknjFSsW4XcuYw4DMPk", "xSOL (USD)"),
         "sol":  ohlcv("58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2", "SOL (USD)")}
    json.dump({"base_mint": PERP_MINT, "pool_name": "PERP / xSOL", "series": s},
              open("data/perp_series.json", "w"))
    print("wrote data/")
