#!/usr/bin/env python3
"""
Round-trip structure across every captured pool.

A round-trip transaction is one that contains BOTH a sell and a buy of the same token
in the same pool. On-chain these carry two signers: one wallet sells, the other buys,
atomically, in a transaction both authorise. There is no price difference to capture
and fees are paid twice, so the only product of the transaction is volume.

The manifest pools are kept in the capture and excluded here: manifest is an order
book, not an AMM, so a zero reserve is expected there and proves nothing.
"""
import json, collections, statistics as st

D = json.load(open("data/trades.json"))
IDX = {p["pool"]: p for p in json.load(open("data/pool_index.json"))["pools"]}
print(f"captured at {D['captured_at']}\n")

rows, excluded = [], []
for pool, info in D["pools"].items():
    meta = IDX.get(pool, {})
    tr = info["trades"]
    if meta.get("dex") != "pumpswap":
        excluded.append((info["name"], meta.get("dex")))
        continue
    if not tr:
        continue
    byhash = collections.defaultdict(list)
    for x in tr:
        byhash[x["tx_hash"]].append(x)
    rt = [h for h, v in byhash.items() if len({e["kind"] for e in v}) > 1]
    vol = sum(float(x["volume_in_usd"] or 0) for x in tr)
    rtvol = sum(float(e["volume_in_usd"] or 0) for h in rt for e in byhash[h])
    dust = [x for x in tr if float(x["volume_in_usd"] or 0) < 0.10]
    dustaddr = {x["tx_from_address"] for x in dust}
    ts = sorted(x["block_timestamp"] for x in tr)
    rows.append({
        "name": info["name"], "pool": pool, "n": len(tr), "tx": len(byhash),
        "rt": len(rt), "rt_share": len(rt) / len(byhash),
        "vol": vol, "rt_vol_share": rtvol / vol if vol else 0,
        "dust": len(dust), "dust_addr": len(dustaddr),
        "addrs": len({x["tx_from_address"] for x in tr}),
        "span_s": len(set(ts)), "first": ts[0], "last": ts[-1],
        "vol24h": float(meta.get("vol24h") or 0),
    })

print(f"{'pool':<18}{'tx':>6}{'round-trip':>12}{'% of tx':>9}{'% of volume':>13}{'addrs':>7}{'dust':>6}")
for r in sorted(rows, key=lambda x: -x["vol24h"]):
    print(f"{r['name'][:17]:<18}{r['tx']:>6}{r['rt']:>12}{r['rt_share']*100:>8.0f}%"
          f"{r['rt_vol_share']*100:>12.1f}%{r['addrs']:>7}{r['dust']:>6}")

shares = [r["rt_vol_share"] for r in rows]
tsh = [r["rt_share"] for r in rows]
print(f"\npools measured: {len(rows)}   sampled trades: {sum(r['n'] for r in rows):,}")
print(f"round-trip share of transactions: median {st.median(tsh)*100:.0f}%, "
      f"min {min(tsh)*100:.0f}%, max {max(tsh)*100:.0f}%")
print(f"round-trip share of VOLUME:       median {st.median(shares)*100:.1f}%, "
      f"min {min(shares)*100:.1f}%, max {max(shares)*100:.1f}%")
print(f"pools where round-trips carry over 99% of sampled volume: "
      f"{sum(1 for s in shares if s > 0.99)} of {len(rows)}")
print(f"\nclaimed 24h volume of these pools: ${sum(r['vol24h'] for r in rows):,.0f}")
print(f"excluded as not-an-AMM: {excluded}")
