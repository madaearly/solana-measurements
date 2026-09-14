#!/usr/bin/env python3
"""
The published figures: 7-day-median endpoints, one method applied to all four assets.

Point-to-point returns are also printed, so the difference the method makes is visible
rather than argued. The medians are the conservative read on every column.
"""
import json, datetime as dt, statistics as st

D = json.load(open("data/final_series.json"))
S = {k: {int(a): b for a, b in v.items()} for k, v in D.items()}


def day(t):
    return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")


sh, sh2, sol, hy, xs = S["sh"], S["sh2"], S["sol"], S["hy"], S["xsol"]
common = sorted(set(sh) & set(sol) & set(xs) & set(hy))
f, l = common[0], common[-1]
W = 7
print(f"window {day(f)} -> {day(l)}, {len(common)} shared days\n")


def med(series, keys):
    return st.median([series[k] for k in keys if k in series])


print("=== sHYUSD: point endpoints against 7-day medians ===")
print(f"  point to point : {sh[f]:.4f} -> {sh[l]:.4f}   = {(sh[l] / sh[f] - 1) * 100:+.2f}%")
h = med(sh, sorted(sh)[:W]); t = med(sh, sorted(sh)[-W:])
print(f"  medians        : {h:.4f} -> {t:.4f}   = {(t / h - 1) * 100:+.2f}%")
h2 = med(sh2, sorted(sh2)[:W]); t2 = med(sh2, sorted(sh2)[-W:])
print(f"  the ONe pool   : {h2:.4f} -> {t2:.4f}   = {(t2 / h2 - 1) * 100:+.2f}%")
yrs = (l - f) / 86400 / 365
print(f"  annualised on medians: {((t / h) ** (1 / yrs) - 1) * 100:+.2f}%")

print("\n=== four outcomes over the shared window, 7-day medians at both ends ===")
for lab, s in (("SOL", sol), ("xSOL", xs), ("hyUSD", hy), ("sHYUSD", sh)):
    ks = [k for k in common if k in s]
    a = st.median([s[k] for k in ks[:W]])
    b = st.median([s[k] for k in ks[-W:]])
    print(f"  $1,000 in {lab:<7} -> ${1000 * b / a:>9,.2f}   ({(b / a - 1) * 100:+.2f}%)"
          f"   point to point ${1000 * s[l] / s[f]:>9,.2f}")
