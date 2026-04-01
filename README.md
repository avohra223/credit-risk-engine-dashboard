# Credit Risk Engine

Production-grade credit risk modelling platform simulating a Corporate & Investment Banking risk function for a mixed European lending portfolio.

---

## Architecture

```
                    +------------------+
                    |     main.py      |   Orchestrator
                    +--------+---------+
                             |
            +----------------+----------------+
            |                |                |
   +--------v------+ +------v-------+ +------v-------+
   | Data Generator | |  Risk Models | |  Portfolio   |
   | (250 obligors, | | PD / LGD /   | |  Analytics   |
   |  400 facilities)| | EAD          | | EL/VaR/RWA  |
   +--------+------+ +------+-------+ +------+-------+
            |                |                |
            v                v                v
   +--------+----------------+----------------+-------+
   |                   SQLite Database                 |
   |               (credit_risk.db)                    |
   +--------+----------------+----------------+-------+
            |                |                |
   +--------v------+ +------v-------+ +------v-------+
   |  Migration    | |   Stress     | |  Streamlit   |
   |  Matrices     | |   Testing    | |  Dashboard   |
   +---------------+ +--------------+ +--------------+
```

## Modules

| Module | Description |
|--------|-------------|
| **PD Model** | Logistic regression predicting 1-year PD with scorecard mapping |
| **LGD Model** | Collateral-based LGD with beta-distributed CIs and downturn adjustment |
| **EAD Model** | CCF-based exposure at default for drawn and contingent facilities |
| **Portfolio Analytics** | EL calculation, Monte Carlo Credit VaR, HHI concentration, IRB RWA |
| **Migration Matrices** | 8x8 transition matrix, cumulative defaults, time-to-default |
| **Stress Testing** | Three EBA-style scenarios with GDP/unemployment/rate/collateral shocks |
| **Dashboard** | 5-page Streamlit app with interactive charts and SQL explorer |

## Quick Start

### Prerequisites
- Python 3.10+

### Installation
```bash
git clone https://github.com/yourusername/credit-risk-engine.git
cd credit-risk-engine
pip install -r requirements.txt
```

### Run the Full Pipeline
```bash
python main.py
```
This generates synthetic data, trains all models, runs portfolio analytics, executes stress tests, and produces outputs.

### Launch the Dashboard
```bash
streamlit run dashboard/app.py
```

### Run Tests
```bash
python -m pytest tests/ -v
```

## Technical Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Models | scikit-learn, scipy, statsmodels |
| Data | pandas, numpy, SQLite |
| Visualisation | plotly, matplotlib, seaborn |
| Dashboard | Streamlit |
| Testing | pytest |

## Portfolio

The synthetic portfolio models a European CIB lending book:
- **250 obligors** across 8 sectors and 7 countries
- **~400 facilities** including term loans, revolvers, bonds, guarantees
- **4 segments**: Large Corporate (40%), Leveraged Finance (25%), Project Finance (20%), Structured Finance (15%)
- Ratings from AAA to CCC with realistic financial ratio profiles

## Model Methodology

Detailed methodology documentation is available in [`docs/model_methodology.md`](docs/model_methodology.md). Key approaches:

- **PD**: Logistic regression on financial ratios + rating notch, calibrated to long-run default rates
- **LGD**: Seniority-based with collateral haircuts (RE: 30%, Equipment: 50%, Financial: 15%, Unsecured: 100%)
- **EAD**: Regulatory CCF approach (Revolvers: 75%, Guarantees: 50%, Trade Finance: 20%)
- **VaR**: Single-factor Gaussian copula, 10,000 Monte Carlo simulations, Basel II correlation
- **Stress**: EBA 2023-aligned scenarios with multi-channel transmission (GDP, unemployment, rates, collateral)

## Regulatory Context

This engine implements concepts from:
- **Basel III IRB Framework** (CRR Articles 142-191): PD/LGD/EAD estimation, RWA calculation
- **EBA Stress Testing Guidelines** (2023 EU-wide methodology): Scenario design, transmission mechanisms
- **IFRS 9 / ECL concepts**: Forward-looking PD estimation, lifetime expected credit losses
- **CRR Collateral Recognition** (Articles 194-217): Haircut framework, eligible collateral types

## Sample Dashboard

The dashboard provides five interactive pages:
1. **Portfolio Overview** - KPIs, sector/rating/geographic exposure charts
2. **Risk Models** - PD distribution, ROC curve, LGD/EAD breakdowns
3. **Portfolio Risk** - Loss distribution with VaR lines, EL waterfall, concentration metrics
4. **Migration & Stress Testing** - Transition heatmap, cumulative default curves, scenario comparison
5. **SQL Explorer** - 15 pre-built analytical queries with results display

## Limitations & Future Work

- **PD model**: Logistic regression serves as a baseline; production would use gradient boosting or neural networks with time-series features
- **Data**: Synthetic portfolio; real implementation would ingest market data (CDS spreads, equity prices) and internal default histories
- **LGD**: Static collateral values; production model would mark-to-market collateral with property indices
- **Correlation**: Single-factor model; multi-factor copula with sector/geographic factors would improve tail risk capture
- **Stress testing**: Fixed multipliers; econometric satellite models linking macro variables to PD/LGD would be more granular
- **Reporting**: Would add automated PDF/XBRL regulatory report generation (COREP, Pillar 3 disclosures)
- **Infrastructure**: Production deployment would use PostgreSQL, Airflow for scheduling, and MLflow for model registry

## Documentation

- [`docs/model_methodology.md`](docs/model_methodology.md) - Detailed model specifications
- [`docs/data_dictionary.md`](docs/data_dictionary.md) - Field-level data documentation
- [`docs/validation_report.md`](docs/validation_report.md) - Model validation summary
