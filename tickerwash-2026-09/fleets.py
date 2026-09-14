#!/usr/bin/env python3
"""
Who is doing it: cluster the pools by the wallets that round-trip in them.

Two pools are joined when five or more of the same wallets round-trip in both. The
connected components are the fleets. Offline; reads only data/trades.json.

Sampling note that matters: each pool's sample is its last 300 trades. A fleet larger
than the sample could not be fully resolved -- but one pool resolves 49 distinct
round-trip wallets, so the sample is not capped at 20, and a fleet of exactly 20
appearing in 25 separate pools is a property of the fleets, not of the sample.
"""
import json, collections, itertools

D = json.load(open("data/trades.json"))
IDX = {p["pool"]: p for p in json.load(open("data/pool_index.json"))["pools"]}

pools, vol = {}, {}
for pool, info in D["pools"].items():
    if IDX.get(pool, {}).get("dex") != "pumpswap":
        continue
    byhash = collections.defaultdict(list)
    for x in info["trades"]:
        byhash[x["tx_hash"]].append(x)
    rt = set()
    for h, v in byhash.items():
        if len({e["kind"] for e in v}) > 1:
            rt.update(e["tx_from_address"] for e in v)
    if rt:
        k = f"{info['name'].split(' /')[0]}:{pool[:5]}"
        pools[k], vol[k] = rt, float(IDX[pool].get("vol24h") or 0)

sizes = collections.Counter(len(v) for v in pools.values())
print(f"pools with round-trip wallets: {len(pools)}")
print(f"fleet sizes observed: {dict(sorted(sizes.items()))}")
print(f"pools with exactly 20: {sizes[20]}\n")

par = {k: k for k in pools}
def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
for a, b in itertools.combinations(pools, 2):
    if len(pools[a] & pools[b]) >= 5:
        ra, rb = find(a), find(b)
        if ra != rb: par[ra] = rb

cl = collections.defaultdict(list)
for k in pools:
    cl[find(k)].append(k)

print(f"{'fleet':<7}{'pools':>7}{'tickers':>9}{'wallets':>9}{'claimed 24h volume':>21}   tickers")
tot = 0
for i, (_, members) in enumerate(sorted(cl.items(), key=lambda x: -sum(vol[m] for m in x[1])), 1):
    t = sorted({m.split(":")[0] for m in members})
    w = set().union(*[pools[m] for m in members])
    v = sum(vol[m] for m in members); tot += v
    print(f"{i:<7}{len(members):>7}{len(t):>9}{len(w):>9}{v:>21,.0f}   {' '.join(t)}")
shared = sum(1 for a in set().union(*pools.values())
             if sum(1 for v in pools.values() if a in v) > 1)
print(f"\nfleets: {len(cl)}   total claimed volume: ${tot:,.0f}")
print(f"round-trip wallets in total: {len(set().union(*pools.values()))}, "
      f"of which {shared} appear in more than one pool")
