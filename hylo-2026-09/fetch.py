#!/usr/bin/env python3
"""
Pull the five daily close series this measurement rests on, into final_series.json.

GeckoTerminal returns closes already denominated in USD. Do not multiply by a quote
price; that was the first mistake made on this protocol and it cost 48%.

sHYUSD needs `token=<sHYUSD mint>` on the request. Its deepest pool is named
"hyUSD / sHYUSD" and the base side is hyUSD, so without the parameter the endpoint
returns hyUSD's series and it looks plausible.
"""
import json, time, urllib.request, urllib.parse, datetime as dt

UA = {"Accept": "application/json;version=20230302", "User-Agent": "mada/0.1"}
SHYUSD_MINT = "HnnGv3HrSqjRpgdFmx7vQGjntNEoex1SU4e9Lxcxuihz"

POOLS = [
    ("hy",   "4tJW2axbTxtT6nKbjB5pZwePtW84cB7E1B6tdCCLGfrC", "hyUSD/USDC",    None),
    ("sh",   "FsayKGwMGDmfXZrXPWrnzWGLAHLPfQRug28kVL1JT6wR", "sHYUSD (main)", SHYUSD_MINT),
    ("sh2",  "8CA9zadmbpQqoXPXN9Xsk33RVv171sidc8KK1NzVVZbz", "sHYUSD (ONe)",  SHYUSD_MINT),
    ("sol",  "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2", "SOL/USDC",      None),
    ("xsol", "coj59LYbLc6DhMwnxxfPc9mUiknjFSsW4XcuYw4DMPk",  "xSOL",          None),
]


def gt(pool, token=None, before=None):
    q = {"aggregate": 1, "limit": 1000}
    if token:  q["token"] = token
    if before: q["before_timestamp"] = before
    u = ("https://api.geckoterminal.com/api/v2/networks/solana/pools/"
         f"{pool}/ohlcv/day?" + urllib.parse.urlencode(q))
    r = urllib.request.Request(u, headers=UA)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(r, timeout=45) as f:
                return json.load(f)
        except Exception as e:
            if attempt == 4:
                return {"err": repr(e)[:70]}
            time.sleep(6 * (attempt + 1))
    return {}


def pull(pool, label, token=None, pages=4):
    bars, before = {}, None
    for _ in range(pages):
        d = gt(pool, token, before)
        rows = (d.get("data") or {}).get("attributes", {}).get("ohlcv_list")
        if not rows:
            break
        for b in rows:
            if b[4]:
                bars[int(b[0])] = float(b[4])
        oldest = min(int(b[0]) for b in rows)
        if before is not None and oldest >= before:
            break
        before = oldest
        time.sleep(3)
    ks = sorted(bars)
    if ks:
        print(f"  {label:<16} {len(bars):>4} days  "
              f"{dt.datetime.utcfromtimestamp(ks[0]):%Y-%m-%d} -> "
              f"{dt.datetime.utcfromtimestamp(ks[-1]):%Y-%m-%d}  last ${bars[ks[-1]]:.4f}")
    else:
        print(f"  {label:<16} empty")
    return bars


if __name__ == "__main__":
    print("fetching daily closes")
    out = {key: pull(pool, label, token) for key, pool, label, token in POOLS}
    json.dump(out, open("data/final_series.json", "w"))
    print("wrote data/final_series.json")
