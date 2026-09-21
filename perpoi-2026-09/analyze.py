#!/usr/bin/env python3
"""Every figure in the post, from the committed capture, offline."""
import collections, json

core = json.load(open("data/hl_markets.json"))
built = json.load(open("data/hl_builder_dexs.json"))
llama = json.load(open("data/llama_oi.json"))

core_oi = sum(r["oi_usd"] for r in core)
print(f"HYPERLIQUID CORE      {len(core)} markets  ${core_oi:,.0f}")
paxg = next((r for r in core if r["name"] == "PAXG"), None)
spx = next((r for r in core if r["name"] == "SPX"), None)
if paxg:
    print(f"  tokenised gold PAXG ${paxg['oi_usd']:,.0f} = {100*paxg['oi_usd']/core_oi:.3f}% "
          f"— the only real-world asset in the core list")
if spx:
    print(f"  SPX marks at ${spx['px']:.4f} — SPX6900, a memecoin, not the index")

print("\nBUILDER-DEPLOYED VENUES ON THE SAME CHAIN")
tot = sum(v["oi"] for v in built.values())
for k, v in sorted(built.items(), key=lambda kv: -kv[1]["oi"]):
    nz = sum(1 for r in v["markets"] if r["oi_usd"] > 0)
    print(f"  {v['fullName']:24s} ${v['oi']:>15,.0f} {100*v['oi']/tot:>6.1f}%   "
          f"{nz:>3}/{len(v['markets'])} markets carry any")
print(f"  {'TOTAL':24s} ${tot:>15,.0f}")

dead = {k: v for k, v in built.items() if v["oi"] == 0}
dm = sum(len(v["markets"]) for v in dead.values())
dv = sum(sum(r["vol24"] for r in v["markets"]) for v in dead.values())
print(f"\nEMPTY: {len(dead)} venues, {dm} markets, open interest 0, 24h volume {dv:,.2f}")
for v in dead.values():
    print(f"  {v['fullName']:24s} " + " ".join(r["name"].split(":")[-1] for r in v["markets"][:9]))

ps = llama["protocols"]
head = llama["total24h"]
s = sum(p.get("total24h") or 0 for p in ps)
cat = collections.defaultdict(float)
for p in ps:
    cat[p.get("category") or "?"] += p.get("total24h") or 0
print(f"\nDEFILLAMA  headline ${head:,.0f}  sum of {len(ps)} protocols ${s:,.0f}  gap ${s-head:,.0f}")
for k, v in sorted(cat.items(), key=lambda kv: -kv[1]):
    print(f"  {k:28s} ${v:>15,.0f}")
print(f"\n  reporting zero: {sum(1 for p in ps if not (p.get('total24h') or 0))} of {len(ps)}")
