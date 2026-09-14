#!/usr/bin/env python3
"""
Is sHYUSD's daily movement real, or is it the print of a pool nobody trades?

Two tests. Lag-1 autocorrelation of daily returns: strongly negative means bid-ask
bounce around a smoother underlying value. And the variance ratio: daily sigma implied
by blocks of 1, 3, 7 and 14 days. For a real price series those four numbers agree.
For noise around a slow-moving value they fall as the block lengthens.

SOL and xSOL are the controls. Same window, same provider, same code path.
"""
import json, datetime as dt, statistics as st

D = json.load(open("data/final_series.json"))
S = {k: {int(a): b for a, b in v.items()} for k, v in D.items()}


def day(t):
    return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")


sh, sh2, sol, hy = S["sh"], S["sh2"], S["sol"], S["hy"]
ks = sorted(sh)
print("=== last 14 days of sHYUSD in both pools, against SOL ===")
for k in ks[-14:]:
    print(f"  {day(k)}  main {sh[k]:.4f}   ONe {sh2.get(k, float('nan')):.4f}   "
          f"SOL ${sol.get(k, 0):.2f}   hyUSD {hy.get(k, 0):.4f}")


def ac1(x):
    m = st.mean(x); n = len(x)
    num = sum((x[i] - m) * (x[i - 1] - m) for i in range(1, n))
    return num / sum((v - m) ** 2 for v in x)


def rets(s):
    k = sorted(s)
    return [s[k[i]] / s[k[i - 1]] - 1 for i in range(1, len(k))]


print("\n=== lag-1 autocorrelation of daily returns ===")
print(f"  sHYUSD main {ac1(rets(sh)):+.3f}   sHYUSD ONe {ac1(rets(sh2)):+.3f}   "
      f"SOL {ac1(rets(sol)):+.3f}   hyUSD {ac1(rets(hy)):+.3f}")
print("  strongly negative = bounce around a smoother value")


def block(series, n):
    k = sorted(series)
    return [series[k[i]] / series[k[i - n]] - 1 for i in range(n, len(k), n)]


print("\n=== variance ratio: daily sigma implied by 1/3/7/14-day blocks ===")
for lab, s in (("SOL", sol), ("xSOL", S["xsol"]), ("sHYUSD", sh)):
    row = [st.pstdev(block(s, n)) * 100 / (n ** .5) for n in (1, 3, 7, 14)]
    print(f"  {lab:<7} " + "  ".join(f"{v:.2f}%" for v in row))
print("  flat = real. collapsing = noise in the daily prints.")
