#!/usr/bin/env python3
"""
Build the published table: $1,000 in each asset, trailing 7-day median, day by day.

The first W-1 days are consumed by the median, so the series starts a week after the
shared window opens. Writes ledger_series.json (the four columns) and peg_series.json
(hyUSD's full 319 closes, used for the peg chart).
"""
import json, datetime as dt, statistics as st

W = 7
D = json.load(open("data/final_series.json"))
S = {k: {int(a): b for a, b in v.items()} for k, v in D.items()}


def day(t):
    return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")


sh, sol, hy, xs = S["sh"], S["sol"], S["hy"], S["xsol"]
common = sorted(set(sh) & set(sol) & set(xs) & set(hy))
ASSETS = (("sol", sol), ("xsol", xs), ("hy", hy), ("sh", sh))


def tmed(s, keys, i):
    return st.median([s[k] for k in keys[max(0, i - W + 1):i + 1]])


base = {lab: tmed(s, common, W - 1) for lab, s in ASSETS}
series = []
for i, k in enumerate(common):
    if i < W - 1:
        continue
    row = {"d": i, "date": day(k)}
    for lab, s in ASSETS:
        row[lab] = round(1000 * tmed(s, common, i) / base[lab], 2)
    series.append(row)

print("last point:", json.dumps(series[-1]))
for lab, _ in ASSETS:
    vals = [r[lab] for r in series]
    peak, mdd, at = -1e9, 0, None
    for r in series:
        peak = max(peak, r[lab])
        if r[lab] / peak - 1 < mdd:
            mdd, at = r[lab] / peak - 1, r["date"]
    print(f"  {lab:<5} low ${min(vals):>8,.2f}  high ${max(vals):>8,.2f}  "
          f"max drawdown {mdd * 100:>7.2f}% ({at})")
print(f"points: {len(series)}  {series[0]['date']} -> {series[-1]['date']}")

json.dump({"series": series, "start": day(common[0]), "end": day(common[-1]),
           "n_common": len(common)}, open("data/ledger_series.json", "w"))
hk = sorted(hy)
json.dump({"peg": [round(hy[k], 5) for k in hk], "from": day(hk[0]), "to": day(hk[-1])},
          open("data/peg_series.json", "w"))
print(f"wrote data/ledger_series.json and data/peg_series.json ({len(hk)} peg closes)")
