#!/usr/bin/env python3
"""Who holds transferFeeConfigAuthority, across a 3,000-mint sample. No derived figures."""
import collections, json, math

AUTH = "5KXDF6QnqhBj72hDtJNkkpFaQVUfbFXNybMsp3DiK6tD"
PDA = "WLHv2UAZm6z4KyaaELi5pjdbJh6RESMva1Rnn8pJVVh"
d = json.load(open("data/sample.json"))
N = len(d)
pop = sum(1 for _ in open("data/population.txt"))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


buckets = collections.Counter()
rates = collections.Counter()
rates_key = collections.Counter()
withheld_live = 0
for m, r in d.items():
    a = r["fee_authority"]
    if r["fee_bps"] is None:
        buckets["no transfer fee"] += 1
        continue
    rates[r["fee_bps"]] += 1
    if a == AUTH:
        buckets["keypair 5KXDF6"] += 1
        rates_key[r["fee_bps"]] += 1
    elif a == PDA:
        buckets["program WLHv2U"] += 1
    elif a is None:
        buckets["null - frozen"] += 1
    else:
        buckets["some other address"] += 1

print(f"sample {N:,} of a population of {pop:,} Token-2022 mints\n")
print(f"{'who may change the fee':26s} {'mints':>7s} {'share':>8s}   95% interval")
for k, v in buckets.most_common():
    lo, hi = wilson(v, N)
    print(f"  {k:24s} {v:>7,} {100*v/N:7.2f}%   {100*lo:5.2f}% - {100*hi:5.2f}%")
kp = buckets["keypair 5KXDF6"]
lo, hi = wilson(kp, N)
print(f"\nextrapolated to the whole population of {pop:,}:")
print(f"  mints whose fee rate one keypair may change: {int(pop*kp/N):,}"
      f"   ({int(pop*lo):,} - {int(pop*hi):,})")
print(f"\nfee rates across every mint that has one:")
for k, v in sorted(rates.items()):
    print(f"  {k:5d} bps  {v:>6,}  ({100*v/sum(rates.values()):.1f}%)")
print(f"\nfee rates among the {kp:,} the keypair controls:")
for k, v in sorted(rates_key.items()):
    print(f"  {k:5d} bps  {v:>6,}  ({100*v/kp:.1f}%)")
frozen = buckets["null - frozen"]
prog = buckets["program WLHv2U"]
print(f"\nheadline: {100*(frozen+prog)/N:.1f}% of these mints cannot have their rate changed by any"
      f" private key.\n          {100*kp/N:.1f}% can, and it is the same key on all of them.")
