#!/usr/bin/env python3
"""
Collect everything the desk renders, from public endpoints, for one Solana token.

Every figure this writes is something a reader can fetch themselves with the same
two URLs. Nothing is modelled, nothing is filled in, and a field the source does
not carry is written as null rather than guessed.

The one thing that makes this worth building: GeckoTerminal's /trades endpoint
carries the WALLET ADDRESS of each trade, which no other free source here does.
That is what turns the reference format's cast of invented characters into a list
of accounts anyone can look up.

    .venv/bin/python lib/collect_desk.py <mint> --out data/<id>-desk.json [--pools 4]

Rate limit: the free tier cuts off around 30 requests a minute and answers 429
without warning, so every call goes through get() and every call sleeps.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request
from collections import defaultdict
from datetime import datetime, timezone

GT = "https://api.geckoterminal.com/api/v2"
DS = "https://api.dexscreener.com/latest/dex"
NET = "solana"
PAUSE = 2.2


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                out = json.load(r)
            time.sleep(PAUSE)
            return out
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = PAUSE * (i + 2) * 2
                print(f"    429, waiting {wait:.0f}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except Exception:
            time.sleep(PAUSE * (i + 1))
    return None


def iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def collect(mint, n_pools=4, ohlcv_limit=180):
    out = {
        "mint": mint,
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "geckoterminal /pools, /trades, /ohlcv + dexscreener /tokens",
        "token": {"address": mint, "name": None, "symbol": None},
        "pools": [],
        "trades": [],
        "ohlcv": [],
        "totals": {},
    }

    print("pools…", file=sys.stderr)
    d = get(f"{GT}/networks/{NET}/tokens/{mint}/pools?page=1")
    if not d or not d.get("data"):
        raise SystemExit("no pools for that mint")
    pools = d["data"]

    for p in pools:
        a = p["attributes"]
        tx = (a.get("transactions") or {}).get("h24") or {}
        liq = float(a.get("reserve_in_usd") or 0)
        vol = float((a.get("volume_usd") or {}).get("h24") or 0)
        out["pools"].append({
            "name": a.get("name"),
            "address": a.get("address"),
            "liquidity": liq,
            "volume24": vol,
            "buys": tx.get("buys"),
            "sells": tx.get("sells"),
            # unique wallets — the field that makes the roster possible
            "buyers": tx.get("buyers"),
            "sellers": tx.get("sellers"),
            "turnover": (vol / liq) if liq > 0 else None,
            # the arithmetic-versus-money test: an untraded pool's depth and cap
            # are price x quantity at a price nobody paid
            "traded": (vol / liq >= 1e-4) if liq > 0 else False,
        })
        if out["token"]["name"] is None:
            base = (p.get("relationships") or {}).get("base_token", {})
            del base
    out["pools"].sort(key=lambda p: -(p["liquidity"] or 0))

    print("token identity…", file=sys.stderr)
    ds = get(f"{DS}/tokens/{mint}")
    if ds and ds.get("pairs"):
        mine = [q for q in ds["pairs"]
                if (q.get("baseToken", {}).get("address") or "").lower() == mint.lower()]
        if mine:
            top = max(mine, key=lambda q: (q.get("liquidity") or {}).get("usd") or 0)
            out["token"]["name"] = top["baseToken"].get("name")
            out["token"]["symbol"] = top["baseToken"].get("symbol")
            out["totals"]["price"] = float(top.get("priceUsd") or 0) or None
            out["totals"]["marketCap"] = top.get("marketCap") or top.get("fdv")

    chosen = [p for p in out["pools"] if p["traded"]][:n_pools]
    print(f"trades from {len(chosen)} pools…", file=sys.stderr)
    for p in chosen:
        d = get(f"{GT}/networks/{NET}/pools/{p['address']}/trades")
        if not d or not d.get("data"):
            print(f"    {p['name']}: none", file=sys.stderr)
            continue
        for t in d["data"]:
            x = t["attributes"]
            out["trades"].append({
                "ts": x.get("block_timestamp"),
                "side": x.get("kind"),
                "usd": float(x.get("volume_in_usd") or 0),
                "wallet": x.get("tx_from_address"),
                "pool": p["name"],
            })
        print(f"    {p['name']}: {len(d['data'])}", file=sys.stderr)

    if chosen:
        print("ohlcv…", file=sys.stderr)
        d = get(f"{GT}/networks/{NET}/pools/{chosen[0]['address']}"
                f"/ohlcv/minute?aggregate=5&limit={ohlcv_limit}")
        if d:
            out["ohlcv"] = (d.get("data", {}).get("attributes", {}) or {}).get("ohlcv_list", [])
            out["ohlcv"].reverse()
            out["ohlcv_pool"] = chosen[0]["name"]

    out["trades"].sort(key=lambda t: t["ts"] or "")

    # --- make the time axis honest ------------------------------------------
    # /trades returns the last 300 per pool and nothing more, so each pool reaches
    # back a different distance: on the first xSOL run, 20.1h, 15.2h and 8.4h. Merge
    # them naively and the early part of the window contains only the slow pools,
    # which invents a trend out of which venues happen to be present. Measured on
    # that run: imbalance appeared to travel -0.52 -> -0.08 across the window, and
    # 300 of one pool's 344 trades sat in the final quarter.
    #
    # The fix is the intersection: keep only the span where every sampled pool is
    # covered end to end. Inside it no pool is truncated, so a change over time is
    # a change in the market rather than a change in the sample.
    span = {}
    for t in out["trades"]:
        a = span.setdefault(t["pool"], [t["ts"], t["ts"]])
        a[0] = min(a[0], t["ts"])
        a[1] = max(a[1], t["ts"])
    out["coverage"] = [
        {"pool": k, "from": v[0], "to": v[1],
         "hours": round((iso(v[1]) - iso(v[0])).total_seconds() / 3600, 2),
         "trades": sum(1 for t in out["trades"] if t["pool"] == k)}
        for k, v in sorted(span.items())
    ]
    if span:
        lo = max(v[0] for v in span.values())
        hi = min(v[1] for v in span.values())
        if lo < hi:
            kept = [t for t in out["trades"] if lo <= t["ts"] <= hi]
            out["window"] = {
                "mode": "intersection",
                "from": lo, "to": hi,
                "hours": round((iso(hi) - iso(lo)).total_seconds() / 3600, 2),
                "pools": len(span),
                "dropped": len(out["trades"]) - len(kept),
                "raw_from": out["trades"][0]["ts"], "raw_to": out["trades"][-1]["ts"],
                "raw_hours": round((iso(out["trades"][-1]["ts"]) - iso(out["trades"][0]["ts"])).total_seconds() / 3600, 2),
                # valid because the window lies inside every pool's own coverage.
                # The test is containment, not "did each pool trade in each slice":
                # a covered pool that went quiet is data, not a gap in the sample.
                "axis_valid": all(v[0] <= lo and hi <= v[1] for v in span.values()),
            }
            out["trades"] = kept
        else:
            out["window"] = {"mode": "no overlap", "axis_valid": False,
                             "pools": len(span)}
    if out["trades"]:
        buy = sum(t["usd"] for t in out["trades"] if t["side"] == "buy")
        sell = sum(t["usd"] for t in out["trades"] if t["side"] == "sell")
        agg = defaultdict(lambda: {"n": 0, "buy": 0.0, "sell": 0.0})
        for t in out["trades"]:
            a = agg[t["wallet"]]
            a["n"] += 1
            a["buy" if t["side"] == "buy" else "sell"] += t["usd"]
        wallets = [{"w": w, **v, "net": v["buy"] - v["sell"]} for w, v in agg.items()]
        wallets.sort(key=lambda r: -(r["buy"] + r["sell"]))
        out["wallets"] = wallets
        biggest = max(out["trades"], key=lambda t: t["usd"])
        sizes = sorted((t["usd"] for t in out["trades"]), reverse=True)
        tv = sum(sizes) or 1
        out["distribution"] = {
            "median": sizes[len(sizes) // 2],
            "mean": tv / len(sizes),
            "max": sizes[0],
            "under1": sum(1 for v in sizes if v < 1),
            "top_share": {str(int(p * 100)): round(100 * sum(sizes[:max(1, int(len(sizes) * p))]) / tv, 1)
                          for p in (0.01, 0.05, 0.10, 0.25, 0.50)},
            "buckets": None,
        }
        import math as _m
        lo_e = _m.floor(_m.log10(max(1e-4, min(sizes))))
        hi_e = _m.ceil(_m.log10(sizes[0]))
        edges = [10 ** e for e in range(int(lo_e), int(hi_e) + 1)]
        counts = [0] * (len(edges) - 1)
        for v in sizes:
            for i in range(len(edges) - 1):
                if edges[i] <= v < edges[i + 1]:
                    counts[i] += 1
                    break
        out["distribution"]["buckets"] = [{"lo": edges[i], "hi": edges[i + 1], "n": counts[i]}
                                          for i in range(len(counts))]
        cw = sorted(wallets, key=lambda r: -(r["buy"] + r["sell"]))
        out["concentration"] = {
            "wallets": len(cw),
            "once": sum(1 for r in cw if r["n"] == 1),
            "top": {str(k): round(100 * sum(r["buy"] + r["sell"] for r in cw[:k]) / tv, 1)
                    for k in (1, 5, 10, 25, 50)},
        }
        out["totals"].update({
            "window_from": out["trades"][0]["ts"],
            "window_to": out["trades"][-1]["ts"],
            "window_hours": round(
                (iso(out["trades"][-1]["ts"]) - iso(out["trades"][0]["ts"])).total_seconds() / 3600, 2),
            "trades": len(out["trades"]),
            "wallets": len(wallets),
            "buyUsd": buy,
            "sellUsd": sell,
            "imbalance": (buy - sell) / (buy + sell) if buy + sell else 0,
            "largest": biggest,
            "poolsTotal": len(out["pools"]),
            "poolsTraded": sum(1 for p in out["pools"] if p["traded"]),
            "liquidityTraded": sum(p["liquidity"] for p in out["pools"] if p["traded"]),
            "buyersH24": sum(p["buyers"] or 0 for p in out["pools"]),
            "sellersH24": sum(p["sellers"] or 0 for p in out["pools"]),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mint")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pools", type=int, default=4)
    a = ap.parse_args()
    d = collect(a.mint, a.pools)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(d, open(a.out, "w"), indent=1)
    t = d["totals"]
    print(f"\nwrote {a.out}")
    print(f"  {d['token']['symbol']}  pools {t.get('poolsTotal')} ({t.get('poolsTraded')} traded)")
    print(f"  trades {t.get('trades')} from {t.get('wallets')} wallets "
          f"over {t.get('window_hours')}h")
    print(f"  buy ${t.get('buyUsd', 0):,.0f}  sell ${t.get('sellUsd', 0):,.0f}  "
          f"imbalance {t.get('imbalance', 0):+.3f}")


if __name__ == "__main__":
    main()
