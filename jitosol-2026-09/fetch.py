#!/usr/bin/env python3
"""
Pull jitoSOL and SOL daily closes into data/jito_series.json.

Three jitoSOL pools are fetched, not one, so the price series can be checked against
two independent venues before any figure is derived from it.

jitoSOL needs `token=J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn` on the request.
Every close comes back denominated in USD; the quantity this measurement is actually
about is jitoSOL priced in SOL, which analyze.py derives by division.
"""
import json, time, urllib.request, urllib.parse, datetime as dt

UA = {"Accept": "application/json;version=20230302", "User-Agent": "mada/0.1"}
JITO = "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn"
POOLS = [
    ("jito_orca", "Hp53XEtt4S8SvPCXarsLSdGfZBuUr5mMmZmX2DRNXQKp", "JitoSOL/SOL orca", JITO),
    ("jito_ray",  "2uoKbPEidR7KAMYtY4x7xdkHXWqYib5k4CutJauSL3Mc", "JitoSOL/SOL raydium", JITO),
    ("jito_usdc", "5hWJUNTtEtKmKgDXpthJXXRRmJrz5vJ7uJzrUNVdrwLg", "JitoSOL/USDC orca", JITO),
    ("sol",       "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2", "SOL/USDC raydium", None),
]


def gt(pool, token=None, before=None):
    q = {"aggregate": 1, "limit": 1000}
    if token:  q["token"] = token
    if before: q["before_timestamp"] = before
    u = ("https://api.geckoterminal.com/api/v2/networks/solana/pools/"
         f"{pool}/ohlcv/day?" + urllib.parse.urlencode(q))
    r = urllib.request.Request(u, headers=UA)
    for a in range(5):
        try:
            with urllib.request.urlopen(r, timeout=45) as f:
                return json.load(f)
        except Exception as e:
            if a == 4: return {"err": repr(e)[:70]}
            time.sleep(7 * (a + 1))
    return {}


def pull(pool, label, token=None, pages=4):
    bars, before = {}, None
    for _ in range(pages):
        d = gt(pool, token, before)
        rows = (d.get("data") or {}).get("attributes", {}).get("ohlcv_list")
        if not rows: break
        for b in rows:
            if b[4]: bars[int(b[0])] = float(b[4])
        old = min(int(b[0]) for b in rows)
        if before is not None and old >= before: break
        before = old
        time.sleep(3)
    ks = sorted(bars)
    print(f"  {label:<22} {len(bars):>5} days  "
          f"{dt.datetime.utcfromtimestamp(ks[0]):%Y-%m-%d} -> "
          f"{dt.datetime.utcfromtimestamp(ks[-1]):%Y-%m-%d}" if ks else f"  {label}: empty")
    return bars


if __name__ == "__main__":
    out = {k: pull(pool, label, token) for k, pool, label, token in POOLS}
    json.dump(out, open("data/jito_series.json", "w"))
    print("wrote data/jito_series.json")
