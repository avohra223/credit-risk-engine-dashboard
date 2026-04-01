# Data Dictionary

## Table: `obligors`

| Field | Type | Description | Valid Range |
|-------|------|-------------|-------------|
| `obligor_id` | TEXT (PK) | Unique obligor identifier | OBL-0001 to OBL-0250 |
| `obligor_name` | TEXT | Fictional company name | Non-empty string |
| `segment` | TEXT | Portfolio segment | large_corporate, leveraged_finance, project_finance, structured_finance |
| `sector` | TEXT | Industry sector | Energy, TMT, Healthcare, Industrials, Real Estate, Financial Institutions, Infrastructure, Consumer |
| `country` | TEXT | Country of incorporation | France, Germany, United Kingdom, Netherlands, Spain, Italy, Other |
| `internal_rating` | TEXT | Internal credit rating | AAA, AA, A, BBB, BB, B, CCC, D |
| `annual_revenue` | REAL | Annual revenue (EUR M) | >= 0 |
| `total_assets` | REAL | Total assets (EUR M) | > 0 |
| `total_debt` | REAL | Total outstanding debt (EUR M) | >= 0 |
| `ebitda` | REAL | Earnings before interest, tax, depreciation & amortisation (EUR M) | Can be negative for distressed names |
| `interest_expense` | REAL | Annual interest expense (EUR M) | > 0 |
| `current_assets` | REAL | Current assets (EUR M) | >= 0 |
| `current_liabilities` | REAL | Current liabilities (EUR M) | > 0 |
| `leverage_ratio` | REAL | total_debt / total_assets | 0.0 - 1.0 |
| `interest_coverage` | REAL | ebitda / interest_expense | Can be < 1.0 for distressed |
| `current_ratio` | REAL | current_assets / current_liabilities | 0.4 - 2.5 |
| `debt_to_ebitda` | REAL | total_debt / ebitda | 0.5 - 20.0+ |

## Table: `facilities`

| Field | Type | Description | Valid Range |
|-------|------|-------------|-------------|
| `facility_id` | TEXT (PK) | Unique facility identifier | FAC-00001 to FAC-xxxxx |
| `obligor_id` | TEXT (FK) | References obligors.obligor_id | Valid obligor_id |
| `facility_type` | TEXT | Type of credit facility | term_loan, revolver, guarantee, trade_finance, bond, structured_note |
| `commitment_amount` | REAL | Total committed amount (EUR M) | > 0 |
| `drawn_amount` | REAL | Currently drawn amount (EUR M) | >= 0, <= commitment_amount |
| `undrawn_amount` | REAL | Available undrawn portion (EUR M) | >= 0 |
| `maturity_date` | TEXT | Facility maturity date (ISO 8601) | Future or past date |
| `seniority` | TEXT | Claim priority in default | senior_secured, senior_unsecured, subordinated |
| `collateral_type` | TEXT | Type of collateral pledged | real_estate, equipment, financial_assets, unsecured |
| `collateral_value` | REAL | Appraised collateral value (EUR M) | >= 0 |
| `interest_rate` | REAL | Contractual interest rate | > 0 (typically 1-10%) |
| `origination_date` | TEXT | Facility origination date (ISO 8601) | Past date |
| `governing_law` | TEXT | Legal jurisdiction | English, French, German, Dutch, Spanish, Italian, New York |

## Relationships

- Each **obligor** has 1-4 **facilities** (average ~1.6)
- `facilities.obligor_id` -> `obligors.obligor_id` (foreign key)
- Constraint: `drawn_amount + undrawn_amount <= commitment_amount`

## Computed Fields (Model Output)

| Field | Source | Description |
|-------|--------|-------------|
| `pd_score` | PD Model | 1-year probability of default (0.0001 - 0.9999) |
| `lgd` | LGD Model | Point-in-time loss given default (0.05 - 0.99) |
| `lgd_downturn` | LGD Model | Downturn-adjusted LGD (lgd * 1.25, capped at 1.0) |
| `ead` | EAD Model | Exposure at default = drawn + CCF * undrawn |
| `el` | Portfolio | Expected loss = PD * LGD * EAD |
| `rwa` | RWA Module | Risk-weighted assets per IRB formula |
