# FRE-GY 9743 - Assignment 6

**Aditya Amit Shah | as22008**

The [completed, executed notebook](hw6_interest_rate_products.ipynb) includes
all three written answers, the supplied computational exercises, saved
cashflow tables, formula checks, and factory comparisons.

- [Readable HTML copy](submission/Assignment_6_as22008.html)
- [Four-page solution report](output/pdf/Assignment_6_Solution_as22008.pdf)
- [Editable written solution](submission/Assignment_6_Written_Solution_as22008.md)

## Written solution

The position receives EUR and pays USD at a common maturity, with GBP cash
collateral. The solution derives the value and fair strike using the EUR
and USD discount curves under GBP collateral. It states the FX quotation
and bracket-curve conventions explicitly.

The five supplied curves suffice under a deterministic, consistent
collateral-basis conversion, given spot FX. Without a collateral-switch
assumption they do not uniquely determine the required GBP-collateral curves.
Both full discount-factor and basis-only interpretations of the bracket
notation are covered. A synthetic numerical example checks the conversion,
fair-strike zero PV, and off-market PV sign. It is separate from the starter's
swap inputs.

## Implementation

All six assigned TODO blocks are complete:

1. Fixed and compounded overnight legs for the RFR swap.
2. Both overnight basis-swap legs, with the quoted spread only on leg 1.
3. Convention-driven RFR swap creation.
4. Convention-driven overnight basis-swap creation.
5. Signed RFR swap PV and cash aggregation.
6. Signed basis-swap index, spread and reference-leg PV and cash aggregation.

The supplied FRA and stream engines are reused. Each floating index uses its
own projection curve, and all payments discount with the funding curve.
Spreads are added outside overnight compounding. Receive means receive fixed
for the RFR swap, and receive SOFR plus spread for the supplied basis swap.
Factory axes support spot tenors, start-offset times tenor, and explicit dates;
`3Mx1Y` runs for one year from the forward start. The starter's inputs remain
unchanged.

## Default results

Value date: 2026-01-02. Notional: USD 1,000,000.

| Product / leg | PV (USD) |
| --- | ---: |
| FRA, receive fixed | 87.090294207 |
| RFR fixed leg | 38,534.539463150 |
| RFR floating leg | 41,164.219037938 |
| RFR swap, receive fixed | -2,629.679574788 |
| Basis leg 1, SOFR plus spread | 42,163.002863421 |
| Basis leg 2, Fed Funds | 33,716.530392254 |
| Basis swap, receive leg 1 | 8,446.472471167 |

## Run and verify

Use the starter's recommended Python 3.11 environment:

```sh
python -m pip install -r requirements.txt
jupyter notebook hw6_interest_rate_products.ipynb
python -m unittest discover -s tests -v
```

Restart the notebook kernel and run every cell after any library edits.
All 18 code cells executed successfully from a fresh kernel. All 13
independent tests in `tests/test_interest_rate_products.py` passed.

Tests cover closed-form flat-curve PVs, distinct projection and funding
rates, fixed versus floating day counts, spread placement, pay/receive
signs, same-day cash, expired cashflows, payment lag, repeated valuation,
schedule frequencies, factory conventions and dates, serialization, and
signed cashflow-report reconciliation.

Local validation used Python 3.13.6, NumPy 2.3.2, pandas 2.3.1, and QuantLib 1.41.
The starter's pinned NumPy version targets Python 3.11; the actual local run
used compatible installed Python 3.13 packages. The supplied requirements
were preserved for course reproducibility.

## Project and submission

Starter: [Jerry0108-SJ/FRE-GY-9743-Assignments-6](https://github.com/Jerry0108-SJ/FRE-GY-9743-Assignments-6).

Keep the complete project together for a code submission; the notebook imports
the accompanying library. The solution is published on the personal branch
[`Aditya_Shah_Branch`](https://github.com/Aditya8321/FRE-GY-9743-Assignments-6/tree/Aditya_Shah_Branch)
in the student fork. Submit that branch link through Brightspace.
Brightspace submission remains a separate step.
