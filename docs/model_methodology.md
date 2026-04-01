# Model Methodology

## 1. Probability of Default (PD) Model

### Specification
Logistic regression predicting 1-year probability of default for corporate obligors.

### Features
| Feature | Description | Rationale |
|---------|-------------|-----------|
| `leverage_ratio` | Total Debt / Total Assets | Core solvency indicator |
| `interest_coverage` | EBITDA / Interest Expense | Debt serviceability measure |
| `current_ratio` | Current Assets / Current Liabilities | Short-term liquidity proxy |
| `debt_to_ebitda` | Total Debt / EBITDA | Cash flow leverage |
| `sector_risk_score` | Sector-level risk score (1-10) | Captures industry cyclicality |
| `rating_notch` | Numeric encoding of internal rating | Ordinal credit quality |

### Calibration
- Training data: 250 obligors with binary default indicator derived from rating-implied PDs
- Class weighting applied to handle low default rates (~2-3%)
- Final PD blended: 60% model output + 40% rating-implied PD for realistic calibration
- PD floored at 1bp (AAA) and capped at 99.99%

### Discriminatory Power Metrics
- **AUC (Area Under ROC Curve)**: Target > 0.75
- **Gini Coefficient**: 2 * AUC - 1
- **Kolmogorov-Smirnov (KS) Statistic**: Maximum separation between default and non-default CDFs
- **Hosmer-Lemeshow Test**: Goodness-of-fit across decile buckets

### Scorecard
PD bands mapped to 8 internal rating grades (AAA through D) with monotonically increasing average PDs.

---

## 2. Loss Given Default (LGD) Model

### Specification
Collateral-based LGD estimation with beta-distributed confidence intervals.

### Methodology
1. **Base LGD** from seniority: Senior Secured (25%), Senior Unsecured (45%), Subordinated (70%)
2. **Collateral benefit** reduces base LGD proportional to coverage ratio after haircuts
3. **Collateral haircuts**: Real Estate (30%), Equipment (50%), Financial Assets (15%), Unsecured (100%)
4. **Sector adjustment**: Cyclical sectors receive a slight uplift
5. **Confidence intervals** via Beta distribution parametrised around point estimate

### Downturn Adjustment
Per CRR Article 181(1)(b), downturn LGD applies a **1.25x multiplier** to through-the-cycle estimates. This captures the empirical observation that recovery rates decline during economic downturns due to:
- Depressed collateral values
- Lower secondary market liquidity
- Extended workout timelines

### Output Range
- Senior Secured with Real Estate: 5-20%
- Senior Unsecured: 35-55%
- Subordinated Unsecured: 60-80%

---

## 3. Exposure at Default (EAD) Model

### Specification
Credit Conversion Factor (CCF) approach for off-balance sheet items.

### Formula
```
EAD = Drawn Amount + CCF * Undrawn Amount
```

### CCF Parameters
| Facility Type | CCF | Regulatory Basis |
|---------------|-----|------------------|
| Term Loan | 100% | Fully drawn at origination |
| Revolver | 75% | CRR Article 166(8) |
| Guarantee | 50% | CRR Article 111 |
| Trade Finance | 20% | Low-risk short-term |
| Bond | 100% | Fixed obligation |
| Structured Note | 100% | Fixed obligation |

---

## 4. Credit VaR (Monte Carlo)

### Model
Single-factor Gaussian copula with asset correlation per Basel II IRB formula.

### Correlation Parameterisation
```
R(PD) = 0.12 * (1 - exp(-50*PD)) / (1 - exp(-50)) + 0.24 * (1 - (1 - exp(-50*PD)) / (1 - exp(-50)))
```

Higher-PD obligors receive lower correlation (idiosyncratic risk dominates), while investment-grade names are more correlated with the systematic factor.

### Simulation
- 10,000 Monte Carlo paths
- Each path: draw systematic factor Z ~ N(0,1), then per-obligor idiosyncratic shocks
- Default if asset value falls below Phi^{-1}(PD)
- Loss = sum of (default_i * LGD_i * EAD_i)
- Output: 95th and 99.9th percentile losses

---

## 5. Risk-Weighted Assets (IRB Formula)

### Basel III Foundation IRB
```
K = [LGD * N((1-R)^{-0.5} * G(PD) + (R/(1-R))^{0.5} * G(0.999)) - PD * LGD]
    * (1 - 1.5*b)^{-1} * (1 + (M - 2.5) * b) * 1.06
RWA = K * 12.5 * EAD
```

Where:
- b(PD) = (0.11852 - 0.05478 * ln(PD))^2 (maturity adjustment)
- M = 2.5 years (assumed effective maturity)
- 1.06 = Basel III scaling factor

---

## 6. Stress Testing

### Scenario Design
Three EBA-style macroeconomic scenarios aligned with the 2023 EU-wide stress test methodology.

### Transmission Mechanism
1. **GDP shock** -> Direct PD multiplier (1.0x / 1.8x / 3.0x)
2. **Unemployment shock** -> Sector-specific PD adjustment via unemployment sensitivity coefficients
3. **Interest rate shock** -> ICR degradation -> PD uplift (~3x leverage on rate sensitivity)
4. **Collateral value shock** -> LGD increase (0% / -15% / -30% on real estate)

All shocks are applied multiplicatively to baseline PD/LGD, with floors and caps to ensure economic reasonableness.
