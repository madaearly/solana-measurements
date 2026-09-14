# Method

Rules that apply to every measurement in this repository.

## 1. Raw data is committed

Every directory carries the raw fetch it was derived from, so any figure can be
re-derived without an API call and without trusting this repository's arithmetic. If
the raw data is too large to commit, the measurement does not go here.

## 2. The script that made the number is committed next to it

No figure appears in a README that is not produced by a script in the same directory.
Running the scripts in the order given in that README reproduces the README.

## 3. Windows are stated, and they are not chosen

A measurement window is set by data availability — when a pool opened, when a token
first traded — and the README says which. Where a window could have been chosen, the
choice and the reason are written down.

## 4. Denomination is checked, not assumed

GeckoTerminal returns closes in USD. Multiplying them by a quote price produces a
number that looks reasonable and is wrong by the quote asset's return. Pool names are
base-first, so a pool named "A / B" returns A's series unless `token=` says otherwise.
Both of these have already produced published-adjacent errors; both are now checked
against an independent source before any figure is written.

## 5. A price is only a measurement if somebody trades it

Before a price series is used, it is tested for whether it moves or whether its prints
do. Two tests, both cheap:

- **Lag-1 autocorrelation of daily returns.** Strongly negative means bounce around a
  smoother underlying value.
- **Variance ratio.** Daily sigma implied by blocks of 1, 3, 7 and 14 days. A real
  series gives roughly the same answer at every horizon. Noise around a slow-moving
  value gives a falling one.

Both tests are run against controls from the same window, the same provider and the
same code path, so a collapse cannot be blamed on the method.

Where a series fails, the measurement is not abandoned — it is restated on a statistic
that survives, and the failure is written into the README.

## 6. Cross-check against an independent pool

A token's series is compared with the same token in a different pool on a different
venue. The README reports the median disagreement and the maximum, not just that a
check was done.

## 7. Withdrawn figures stay visible

Numbers that did not survive checking are named in the README, with what was wrong and
what caught it. They are not quietly deleted. A repository that only contains its
author's successes is not evidence of anything.
