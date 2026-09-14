#!/usr/bin/env python3
"""
Peg statistics, the cross-pool check on sHYUSD, and point-to-point returns.

These are the raw, unsmoothed figures. The headline numbers published alongside this
repository use 7-day medians instead; see robust.py for why, and README.md for what
had to be withdrawn.
"""
import json, datetime as dt, statistics as st

D = json.load(open("data/final_series.json"))
S = {k: {int(a): b for a, b in v.items()} for k, v in D.items()}


def day(t):
    return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")


for k in ("hy", "sh", "sh2", "sol", "xsol"):
    ks = sorted(S[k])
    print(f"{k:<5} {len(ks):>4}d  {day(ks[0])} -> {day(ks[-1])}  last {S[k][ks[-1]]:.4f}")

# --- hyUSD peg, full window -------------------------------------------------
hy = S["hy"]; ks = sorted(hy); v = [hy[k] for k in ks]; dev = [abs(x - 1) for x in v]
print(f"\n=== hyUSD peg: {len(v)} days, {day(ks[0])} -> {day(ks[-1])}")
print(f"  median {st.median(v):.4f}  min {min(v):.4f} "
      f"({day(min(ks, key=lambda k: hy[k]))})  max {max(v):.4f}")
print(f"  mean deviation {st.mean(dev) * 100:.3f}%   worst {max(dev) * 100:.2f}%")
for th in (0.005, 0.01, 0.02):
    print(f"  days beyond {th * 100:.1f}%: {sum(1 for x in dev if x > th)}")

# --- sHYUSD against an independent pool -------------------------------------
sh, sh2 = S["sh"], S["sh2"]
c = sorted(set(sh) & set(sh2))
if c:
    d = [abs(sh2[k] / sh[k] - 1) for k in c]
    print(f"\n=== sHYUSD cross-checked against the ONe pool: {len(c)} overlapping days")
    print(f"  median disagreement {st.median(d) * 100:.2f}%  max {max(d) * 100:.2f}%")
    sk = sorted(sh)
    big = [sk[i] for i in range(1, len(sk)) if sh[sk[i]] / sh[sk[i - 1]] - 1 < -0.02]
    ok = sorted(sh2); conf = 0
    for k in big:
        if k in sh2:
            i = ok.index(k)
            if i and sh2[k] / sh2[ok[i - 1]] - 1 < -0.01:
                conf += 1
    print(f"  daily drops beyond 2%: {len(big)}, present in the second pool: {conf}")

# --- the shared window ------------------------------------------------------
common = sorted(set(sh) & set(S["sol"]) & set(S["xsol"]) & set(hy))
f, l = common[0], common[-1]
print(f"\n=== shared window: {len(common)} days, {day(f)} -> {day(l)}")
for k in ("sol", "xsol", "hy", "sh"):
    s = S[k]
    print(f"  $1,000 in {k:<5} -> ${1000 * s[l] / s[f]:>10,.2f}   ({(s[l] / s[f] - 1) * 100:+.2f}%)")
print("  cash -> $1,000.00")

# --- sHYUSD risk, on the raw series (see README: these did not survive) ------
sv = [1000 * sh[k] / sh[f] for k in common]
peak, mdd, mddk = -1e9, 0, None
for i, k in enumerate(common):
    peak = max(peak, sv[i])
    d = sv[i] / peak - 1
    if d < mdd:
        mdd, mddk = d, k
print(f"\n=== sHYUSD risk on RAW closes -- withdrawn, see README")
print(f"  max drawdown {mdd * 100:.2f}% ({day(mddk)})")
rs = [(sh[common[i]] / sh[common[i - 1]] - 1) for i in range(1, len(common))]
rsol = [(S["sol"][common[i]] / S["sol"][common[i - 1]] - 1) for i in range(1, len(common))]
worst = min(range(len(rs)), key=lambda i: rs[i])
print(f"  worst day {rs[worst] * 100:+.2f}% ({day(common[worst + 1])}), "
      f"SOL that day {rsol[worst] * 100:+.2f}%")
mx, my = st.mean(rs), st.mean(rsol)
cov = sum((rsol[i] - my) * (rs[i] - mx) for i in range(len(rs))) / len(rs)
var = sum((x - my) ** 2 for x in rsol) / len(rs)
sdx = var ** .5
sdy = (sum((x - mx) ** 2 for x in rs) / len(rs)) ** .5
print(f"  beta to SOL {cov / var:.3f}   correlation {cov / (sdx * sdy):.3f}")
print(f"  daily sigma: SOL {sdx * 100:.2f}%   sHYUSD {sdy * 100:.2f}%")
yrs = (l - f) / 86400 / 365
print(f"\n  sHYUSD annualised, point to point: {((sh[l] / sh[f]) ** (1 / yrs) - 1) * 100:+.2f}%")
