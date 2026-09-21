#!/usr/bin/env python3
"""
Open interest on perpetual DEXs, read from the venues rather than from an aggregator.

Two sources, neither needing a key:

  api.hyperliquid.xyz/info   the venue itself. {"type":"metaAndAssetCtxs"} returns the
                             core market list; {"type":"perpDexs"} returns the venues
                             other people have deployed on the same chain, and each of
                             those needs its own metaAndAssetCtxs call. Missing that
                             second call is what made the first pass at this wrong.

  api.llama.fi/overview/open-interest   the aggregator, for every venue that is not
                             Hyperliquid. Taken as reported and not independently checked.

    python3 fetch.py
"""
import json, time, urllib.request

HL = "https://api.hyperliquid.xyz/info"
LLAMA = "https://api.llama.fi/overview/open-interest"


def hl(body, tries=5):
    for _ in range(tries):
        try:
            req = urllib.request.Request(
                HL, data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json", "User-Agent": "mada/1.0"})
            return json.load(urllib.request.urlopen(req, timeout=40))
        except Exception:
            time.sleep(5)
    raise SystemExit(f"hyperliquid unreachable for {body}")


def markets(dex=None):
    """openInterest is in base units; notional is that times the mark price."""
    body = {"type": "metaAndAssetCtxs"}
    if dex:
        body["dex"] = dex
    meta, ctx = hl(body)
    out = []
    for m, c in zip(meta["universe"], ctx):
        oi = float(c.get("openInterest") or 0)
        px = float(c.get("markPx") or 0)
        out.append({"name": m["name"], "oi_base": oi, "px": px,
                    "oi_usd": oi * px, "vol24": float(c.get("dayNtlVlm") or 0)})
    return out


def main():
    core = markets()
    json.dump(core, open("data/hl_markets.json", "w"))
    print(f"core universe: {len(core)} markets, ${sum(r['oi_usd'] for r in core):,.0f}")

    dexs = [d for d in hl({"type": "perpDexs"}) if d]
    built = {}
    for d in dexs:
        rows = markets(d["name"])
        built[d["name"]] = {"fullName": d["fullName"], "markets": rows,
                            "oi": sum(r["oi_usd"] for r in rows)}
        print(f"  {d['name']:6s} {d['fullName']:24s} {len(rows):>3} markets  "
              f"${built[d['name']]['oi']:>15,.0f}")
        time.sleep(0.4)
    json.dump(built, open("data/hl_builder_dexs.json", "w"))

    req = urllib.request.Request(LLAMA, headers={"User-Agent": "mada/1.0"})
    llama = json.load(urllib.request.urlopen(req, timeout=40))
    json.dump(llama, open("data/llama_oi.json", "w"))
    print(f"defillama: headline ${llama['total24h']:,.0f}, {len(llama['protocols'])} protocols")


if __name__ == "__main__":
    main()
