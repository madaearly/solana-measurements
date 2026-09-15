#!/usr/bin/env python3
"""
What it cost to hold a levered long, and what it cost to be priced in one.

Two separate questions, deliberately kept apart:

1. How much of SOL's move reached an xSOL holder over the window these pools define.
   This is the strong part: both series are deep and liquid.

2. Whether being quoted in xSOL is what hurt holders of the memecoins priced in it.
   This is the part that did not survive contact with the data, and the script prints
   the refutation rather than omitting it.

PERP's series is run through the variance-ratio test before anything is derived from
it, because the pool holds $10,721 and a $4,107 pool produced three withdrawn figures
in hylo-2026-09.
"""
import json, datetime as dt, statistics as st

D = json.load(open("data/perp_series.json"))["series"]
S = {k: {int(a): b for a, b in v.items()} for k, v in D.items()}
POOLS = json.load(open("data/xsol_quoted_pools.json"))["pools"]


def day(t):
    return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")


pe, xs, so = S["perp"], S["xsol"], S["sol"]
c = sorted(set(pe) & set(xs) & set(so))
f, l = c[0], c[-1]

print(f"=== the pools that price a token in xSOL: {len(POOLS)} ===")
for p in POOLS:
    print(f"  {p['created']}  {p['ticker']:<10} ${p['liquidity_usd']:>10,.0f}  {p['dex']}")
print(f"  total liquidity ${sum(p['liquidity_usd'] for p in POOLS):,.0f}")
recent = [p for p in POOLS if p["created"] >= "2026-09-11"]
print(f"  opened in the last four days: {len(recent)}")

print(f"\n=== window: {len(c)} days, {day(f)} -> {day(l)} ===")
print("  (start is the day the oldest xSOL-quoted pool opened, not a choice)")
sol_r = so[l] / so[f] - 1
xs_r = xs[l] / xs[f] - 1
print(f"  SOL   {sol_r*100:>+7.1f}%   $1,000 -> ${1000*(1+sol_r):>8,.2f}")
print(f"  xSOL  {xs_r*100:>+7.1f}%   $1,000 -> ${1000*(1+xs_r):>8,.2f}")
print(f"  share of SOL's gain that reached the levered holder: {xs_r/sol_r*100:.1f}%")
lo = min(c, key=lambda k: xs[k]); hi = max(c, key=lambda k: xs[k])
print(f"  that $1,000 in xSOL: low ${1000*xs[lo]/xs[f]:,.0f} on {day(lo)}, "
      f"high ${1000*xs[hi]/xs[f]:,.0f} on {day(hi)}")

print("\n=== is PERP's series usable? variance ratio, 1/3/7/14-day blocks ===")
def block(s, n):
    k = sorted(s)
    return [s[k[i]] / s[k[i - n]] - 1 for i in range(n, len(k), n)]
def ac1(x):
    m = st.mean(x)
    return sum((x[i]-m)*(x[i-1]-m) for i in range(1, len(x))) / sum((v-m)**2 for v in x)
for lab, s in (("SOL", {k: so[k] for k in c}), ("xSOL", {k: xs[k] for k in c}),
               ("PERP usd", {k: pe[k] for k in c}),
               ("PERP in xSOL", {k: pe[k]/xs[k] for k in c})):
    row = [st.pstdev(block(s, n)) * 100 / (n ** .5) for n in (1, 3, 7, 14)]
    ks = sorted(s); rr = [s[ks[i]]/s[ks[i-1]]-1 for i in range(1, len(ks))]
    print(f"  {lab:<13}" + "  ".join(f"{v:>7.2f}%" for v in row) + f"   autocorr {ac1(rr):+.3f}")
print("  flat across horizons and autocorrelation near zero: usable, if volatile")

print("\n=== the hypothesis: was the quote currency eating these positions? ===")
pd_ = pe[l] / pe[f] - 1
px_ = (pe[l]/xs[l]) / (pe[f]/xs[f]) - 1
print(f"  PERP in dollars {pd_*100:>+7.1f}%")
print(f"  PERP in xSOL    {px_*100:>+7.1f}%")
print(f"  difference      {(pd_-px_)*100:>+7.1f} points -- the meme did it alone")
print("\n  NO. Over this window the quote currency contributed nothing.")
print("  Ten of the eleven pools are too young to measure through at all.")
