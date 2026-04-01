-- ============================================================================
-- Credit Risk Engine — Database Schema
-- ============================================================================
-- Two core tables: obligors (counterparty-level) and facilities (deal-level).
-- Designed for analytical queries supporting PD/LGD/EAD modelling and
-- portfolio-level risk aggregation.
-- ============================================================================

CREATE TABLE IF NOT EXISTS obligors (
    obligor_id          TEXT PRIMARY KEY,
    obligor_name        TEXT NOT NULL,
    segment             TEXT NOT NULL CHECK (segment IN ('large_corporate', 'leveraged_finance', 'project_finance', 'structured_finance')),
    sector              TEXT NOT NULL,
    country             TEXT NOT NULL,
    internal_rating     TEXT NOT NULL CHECK (internal_rating IN ('AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D')),
    annual_revenue      REAL NOT NULL CHECK (annual_revenue >= 0),
    total_assets        REAL NOT NULL CHECK (total_assets > 0),
    total_debt          REAL NOT NULL CHECK (total_debt >= 0),
    ebitda              REAL NOT NULL,
    interest_expense    REAL NOT NULL CHECK (interest_expense > 0),
    current_assets      REAL NOT NULL CHECK (current_assets >= 0),
    current_liabilities REAL NOT NULL CHECK (current_liabilities > 0),
    leverage_ratio      REAL NOT NULL,
    interest_coverage   REAL NOT NULL,
    current_ratio       REAL NOT NULL,
    debt_to_ebitda      REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS facilities (
    facility_id         TEXT PRIMARY KEY,
    obligor_id          TEXT NOT NULL REFERENCES obligors(obligor_id),
    facility_type       TEXT NOT NULL CHECK (facility_type IN ('term_loan', 'revolver', 'guarantee', 'trade_finance', 'bond', 'structured_note')),
    commitment_amount   REAL NOT NULL CHECK (commitment_amount > 0),
    drawn_amount        REAL NOT NULL CHECK (drawn_amount >= 0),
    undrawn_amount      REAL NOT NULL CHECK (undrawn_amount >= 0),
    maturity_date       TEXT NOT NULL,
    seniority           TEXT NOT NULL CHECK (seniority IN ('senior_secured', 'senior_unsecured', 'subordinated')),
    collateral_type     TEXT NOT NULL CHECK (collateral_type IN ('real_estate', 'equipment', 'financial_assets', 'unsecured')),
    collateral_value    REAL NOT NULL CHECK (collateral_value >= 0),
    interest_rate       REAL NOT NULL CHECK (interest_rate > 0),
    origination_date    TEXT NOT NULL,
    governing_law       TEXT NOT NULL,

    CHECK (drawn_amount <= commitment_amount),
    CHECK (drawn_amount + undrawn_amount <= commitment_amount * 1.01)  -- tolerance for rounding
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_facilities_obligor ON facilities(obligor_id);
CREATE INDEX IF NOT EXISTS idx_obligors_rating ON obligors(internal_rating);
CREATE INDEX IF NOT EXISTS idx_obligors_sector ON obligors(sector);
CREATE INDEX IF NOT EXISTS idx_obligors_country ON obligors(country);
CREATE INDEX IF NOT EXISTS idx_facilities_type ON facilities(facility_type);
CREATE INDEX IF NOT EXISTS idx_facilities_maturity ON facilities(maturity_date);
