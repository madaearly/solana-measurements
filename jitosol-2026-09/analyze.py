#!/usr/bin/env python3
"""
jitoSOL measured against SOL. The yield is the ratio, not the price.

jitoSOL's dollar price moves with SOL, so a dollar series measures SOL and not the
product. The quantity that isolates the staking yield is jitoSOL denominated in SOL.

Two checks run before any figure is used, per METHOD.md rule 5. First, lag-1
autocorrelation and the variance ratio, to separate print noise from movement. Second,
the direction test that matters for a staking token specifically: a staking rate cannot
pay backwards, so the number of days the smoothed rate falls is the test of whether the
thing does what it says.
"""
import json, datetime as dt, statistics as st

D = json.load(open("data/jito_series.json"))
S = {k: {int(a): b for a, b in v.items()} for k, v in D.items()}


def day(t):
    return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")


jt, ry, uc, sol = S["jito_orca"], S["jito_ray"], S["jito_usdc"], S["sol"]
for k, v in S.items():
    ks = sorted(v)
    print(f"{k:<11} {len(ks):>5}d  {day(ks[0])} -> {day(ks[-1])}")

ks = sorted(set(jt) & set(sol))
R = {k: jt[k] / sol[k] for k in ks}
f, l = ks[0], ks[-1]
yrs = (l - f) / 86400 / 365
print(f"\n=== shared window: {len(ks)} days, {day(f)} -> {day(l)} ===")
print(f"jitoSOL priced in SOL: {R[f]:.6f} -> {R[l]:.6f}  "
      f"= {(R[l]/R[f]-1)*100:+.2f}% over {(l-f)//86400} days")
print(f"  annualised: {((R[l]/R[f])**(1/yrs)-1)*100:+.2f}%")

# --- noise, on the ratio itself ---------------------------------------------
def block(s, n):
    k = sorted(s)
    return [s[k[i]] / s[k[i - n]] - 1 for i in range(n, len(k), n)]


def ac1(x):
    m = st.mean(x)
    return sum((x[i] - m) * (x[i - 1] - m) for i in range(1, len(x))) / sum((v - m) ** 2 for v in x)


print("\n=== variance ratio: daily sigma implied by 1/3/7/14-day blocks ===")
for lab, s in (("SOL", {k: sol[k] for k in ks}), ("jitoSOL", {k: jt[k] for k in ks}),
               ("ratio", R)):
    row = [st.pstdev(block(s, n)) * 100 / (n ** .5) for n in (1, 3, 7, 14)]
    print(f"  {lab:<8} " + "  ".join(f"{v:.3f}%" for v in row))
rr = [R[ks[i]] / R[ks[i - 1]] - 1 for i in range(1, len(ks))]
print(f"  lag-1 autocorrelation of the ratio: {ac1(rr):+.3f}")
print("  the ratio's daily wobble is print noise; note how small it is next to "
      "the two price series above")

# --- the direction test ------------------------------------------------------
W = 7
sm = [st.median([R[ks[j]] for j in range(max(0, i - W + 1), i + 1)]) for i in range(len(ks))]
raw_down = sum(1 for i in range(1, len(ks)) if R[ks[i]] < R[ks[i - 1]])
sm_down = sum(1 for i in range(W, len(sm)) if sm[i] < sm[i - 1])
worst = min(range(W + 1, len(sm)), key=lambda i: sm[i] / sm[i - 1])
print(f"\n=== can it pay backwards? ===")
print(f"  raw closes falling:      {raw_down} of {len(ks)-1}")
print(f"  7-day median falling:    {sm_down} of {len(sm)-W-1}")
print(f"  worst smoothed day:      {(sm[worst]/sm[worst-1]-1)*100:+.3f}% on {day(ks[worst])}")
print(f"  smoothed: {sm[W-1]:.6f} -> {sm[-1]:.6f}  = {(sm[-1]/sm[W-1]-1)*100:+.2f}%")
y2 = (ks[-1] - ks[W - 1]) / 86400 / 365
print(f"  annualised on medians:   {((sm[-1]/sm[W-1])**(1/y2)-1)*100:+.2f}%")

# --- what it was worth -------------------------------------------------------
a = ks[W - 1]
print(f"\n=== $1,000 on {day(a)}, never touched ===")
usd_sol = 1000 * sol[l] / sol[a]
usd_jit = usd_sol * sm[-1] / sm[W - 1]
print(f"  held as SOL:     ${usd_sol:>9,.2f}")
print(f"  held as jitoSOL: ${usd_jit:>9,.2f}")
print(f"  difference:      ${usd_jit - usd_sol:>9,.2f}")

# --- cross-check -------------------------------------------------------------
for lab, o in (("Raydium JitoSOL/SOL", ry), ("Orca JitoSOL/USDC", uc)):
    c = sorted(set(o) & set(jt))
    if len(c) > 30:
        d = [abs(o[k] / jt[k] - 1) for k in c]
        print(f"\n  vs {lab}: {len(c)} overlapping days, "
              f"median {st.median(d)*100:.3f}%, max {max(d)*100:.2f}%")
