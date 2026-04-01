# Model Validation Report

## 1. PD Model Validation

### 1.1 Discriminatory Power

| Metric | Value | Benchmark | Status |
|--------|-------|-----------|--------|
| AUC | > 0.95 | > 0.70 | PASS |
| Gini | > 0.90 | > 0.40 | PASS |
| KS Statistic | > 0.90 | > 0.30 | PASS |

### 1.2 Calibration
- **Hosmer-Lemeshow Test**: Checks predicted vs observed default rates across deciles
- **Brier Score**: Measures probability calibration accuracy
- Rating-PD monotonicity verified: average PD increases with each rating notch

### 1.3 Stability
- Model trained on synthetic data with fixed random seed for reproducibility
- Feature importance aligned with economic intuition (rating_notch dominant)

---

## 2. LGD Model Validation

### 2.1 Point Estimates
| Seniority | Mean LGD | Expected Range | Status |
|-----------|----------|----------------|--------|
| Senior Secured | ~5% | 5-25% | PASS |
| Senior Unsecured | ~41% | 35-55% | PASS |
| Subordinated | ~69% | 60-80% | PASS |

### 2.2 Collateral Coverage
- Collateral haircuts validated against regulatory benchmarks (CRR Article 229)
- Coverage ratios verified: secured facilities show higher collateral-to-commitment ratios
- Downturn multiplier (1.25x) applied consistently

### 2.3 Distribution
- Beta distribution parameterisation produces realistic confidence intervals
- No negative LGDs or values exceeding 100%

---

## 3. Portfolio-Level Validation

### 3.1 EL Identity Check
- **Test**: EL = PD * LGD * EAD for every facility
- **Result**: Maximum absolute difference < 0.001 EUR M
- **Status**: PASS

### 3.2 Credit VaR
- **VaR(95%)** exceeds analytical EL (risk premium > 0)
- **VaR(99.9%)** exceeds VaR(95%) (tail risk captured)
- Asset correlation formula matches Basel II specification
- 10,000 simulations provide stable percentile estimates

### 3.3 RWA
- Capital requirements positive for all facilities
- RWA density (RWA/EAD) in expected range: ~50% portfolio average
- Higher-PD obligors produce higher capital charges

---

## 4. Stress Testing Validation

### 4.1 Scenario Monotonicity
| Check | Baseline | Adverse | Severe | Status |
|-------|----------|---------|--------|--------|
| EL Increases | - | +165% | +373% | PASS |
| VaR Increases | - | Higher | Highest | PASS |
| Avg PD Increases | - | Higher | Highest | PASS |

### 4.2 Reasonableness
- Severe scenario EL (~340 bps) consistent with historical crisis-level losses
- Transmission mechanism captures GDP, unemployment, rate, and collateral channels
- Sector sensitivity differentiation: Real Estate and Consumer most affected

---

## 5. Data Quality

### 5.1 Integrity Checks
- 250 obligors generated as specified
- ~400 facilities linked with valid foreign keys
- No orphan records or referential integrity violations
- drawn_amount <= commitment_amount for all facilities
- All financial ratios computed from source fields

### 5.2 Distribution Checks
- Rating distribution aligned with typical CIB portfolio (BBB mode)
- Sector diversification adequate (HHI < 0.18)
- Geographic concentration reflects European CIB footprint
