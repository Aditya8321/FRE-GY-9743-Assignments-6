# Assignment 6: Collateralised FX and Interest-Rate Products

**Aditya Amit Shah | as22008**  
FRE-GT-9743 - Special Topics: Models to Markets

The written solution answers all three questions in the assignment PDF. The computational section completes the six assigned library methods and retains the supplied examples and inputs. All code cells below are executed with saved output.


## Written solution - 1. Valuation formula

Let $t$ be the valuation date and $T$ the common settlement date. Write $E=\mathrm{EUR}$, $U=\mathrm{USD}$ and $G=\mathrm{GBP}$. Define:

- $S_t$: spot USD per EUR; $X_t$: spot USD per GBP.
- $N$: EUR notional; $K$: contracted USD per EUR.
- $P^{i\mid k}(t,T)$: the value **in currency $i$** of one unit of $i$ paid at $T$, when the trade is collateralised in currency $k$.

Consider the position receiving $N$ EUR and paying $NK$ USD at $T$. Assume full, symmetric, continuously adjusted cash collateral in GBP, remunerated at SONIA, with zero threshold and minimum transfer amount, and no default, collateral optionality, or transaction costs. The sign reverses for the opposite position. All discount factors below refer to the same $(t,T)$.

The EUR receipt has EUR PV $NP^{E\mid G}$, or USD PV $NS_tP^{E\mid G}$. The USD payment has USD PV $NKP^{U\mid G}$. By linearity,

$$\boxed{V_U^{G}(t)=N\left[S_tP^{E\mid G}(t,T)-KP^{U\mid G}(t,T)\right].}$$

Equivalently, directly in the currency-GBP pricing measure,

$$V_U^{G}(t)=NX_t\,\mathbb E_t^{Q_G}\!\left[\exp\!\left(-\int_t^T c_G(u)\,du\right)\frac{S_T-K}{X_T}\right],$$

where $Q_G$ is the currency-GBP risk-neutral measure and $c_G$ is the GBP collateral remuneration rate (SONIA). The payoff must first be converted into GBP at the **terminal** FX rate. This explains why directly applying the SONIA discount factor to a USD payoff is generally incorrect. Reporting in GBP gives $V_G^{G}=V_U^{G}/X_t$; reporting currency does not change the fair strike.


## Written solution - 2. Fair forward strike

Set the inception PV to zero and solve for the strike:

$$\boxed{K_G^*(t,T)=S_t\frac{P^{E\mid G}(t,T)}{P^{U\mid G}(t,T)}.}$$

Consequently,

$$V_U^{G}(t)=NP^{U\mid G}(t,T)\left[K_G^*(t,T)-K\right].$$

This has the expected sign: for receive-EUR/pay-USD, a contracted strike below the current fair strike gives a positive value. At $T$, both discount factors equal one and the formula reduces to $N(S_T-K)$. A forward-starting FX trade with separate near and far exchanges would require both exchanges; the formula here is for the single settlement specified in the question.


## Written solution - 3. Are the five discount factors sufficient?

**The five curves alone are not sufficient without a collateral-switch assumption. They are sufficient in a deterministic, consistent collateral-basis curve framework, provided spot FX is also known.** The assignment does not define the bracket notation, so the convention must be stated.

First interpret $df^{[i,U]}$ as the **full discount factor** $P^{i\mid U}$. Then the supplied curves are

$$D_G=df^{\mathrm{SONIA}}=P^{G\mid G},\quad D_E=df^{\mathrm{EuroSTR}}=P^{E\mid E},\quad D_U=df^{\mathrm{SOFR}}=P^{U\mid U},$$
$$A_G=df^{[G,U]}=P^{G\mid U},\qquad A_E=df^{[E,U]}=P^{E\mid U}.$$

**Deterministic collateral-basis construction.** Let $r_i$ be the formal currency-$i$ financing/risk-free rate, $c_i$ its collateral remuneration, and $y_i=r_i-c_i$ the collateral funding benefit, and assume the switch spread $b_{U,G}=y_U-y_G$ is deterministic over $[t,T]$. The effective short rate for currency $i$ under collateral $k$ is $r_i-y_k$. Switching USD collateral to GBP therefore adds the same $b_{U,G}$ for every payout currency:

$$P^{i\mid G}=L_{G\leftarrow U}P^{i\mid U},\qquad L_{G\leftarrow U}=\exp\!\left(-\int_t^T b_{U,G}(u)\,du\right).$$

Taking $i=G$ identifies the switch factor from supplied curves:

$$L_{G\leftarrow U}=\frac{D_G}{A_G},\qquad
\boxed{P^{U\mid G}=\frac{D_GD_U}{A_G},\quad P^{E\mid G}=\frac{D_GA_E}{A_G}.}$$

Hence,

$$\boxed{K_G^*=S_t\frac{A_E}{D_U},\qquad V_U^G=N\frac{D_G}{A_G}\left(S_tA_E-KD_U\right).}$$

The common switch factor cancels from the fair strike, but scales an off-market PV. EuroSTR is redundant for this particular calculation because $A_E$ already includes the EUR-versus-USD collateral adjustment; it can be used to extract that adjustment as $A_E/D_E$. SONIA alone cannot discount both currency legs, and using only EuroSTR/SOFR omits cross-currency basis.

**If the bracket curves are basis-only factors instead.** Define $B_{i,U}=P^{i\mid U}/D_i$. If the supplied $df^{[G,U]}$ and $df^{[E,U]}$ mean $B_{G,U}$ and $B_{E,U}$, substitute $A_G=D_GB_{G,U}$ and $A_E=D_EB_{E,U}$. The same construction becomes

$$P^{U\mid G}=\frac{D_U}{B_{G,U}},\qquad P^{E\mid G}=\frac{D_EB_{E,U}}{B_{G,U}},$$
$$K_G^*=S_t\frac{D_EB_{E,U}}{D_U},\qquad V_U^G=\frac{N}{B_{G,U}}\left(S_tD_EB_{E,U}-KD_U\right).$$

**General stochastic qualification.** Without the deterministic/separable switch assumption, the effective discount factor is an expectation of an exponential involving rates and funding spreads. A stochastic switch factor cannot be taken outside that expectation. USD-collateralised curves do not determine the GBP-collateralised EUR and USD discount factors; their joint FX/rate/basis dynamics or the required GBP-collateral curves must also be supplied. FX-forward triangulation uses a common collateral currency and does not itself justify switching collateral. Thus the cancellation above is a consequence of the stated curve model, not a general consequence of no-arbitrage.

The general collateral pricing relation and collateral-specific FX forward are consistent with Fujii and Takahashi, *A General Framework for the Benchmark Pricing in a Fully Collateralized Market*, Theorem 2.1 and Section 5.1, [arXiv:1508.06339](https://arxiv.org/abs/1508.06339). The deterministic switch identities above follow by factoring out the assumed deterministic spread.


### Numerical check of the deterministic construction

The following one-year example is **illustrative**, not additional assignment market data. It checks the full-curve and basis-factor representations, zero PV at the fair strike, and the sign for a receive-EUR forward below the fair strike.

