-- ============================================================================
-- Facilities Maturing Within 12 Months
-- ============================================================================
-- Lists facilities approaching maturity that will require refinancing
-- or repayment. Critical for liquidity risk management and for
-- identifying obligors that may face refinancing risk.
-- ============================================================================

SELECT
    f.facility_id,
    o.obligor_name,
    o.internal_rating,
    o.sector,
    f.facility_type,
    f.maturity_date,
    ROUND(f.commitment_amount, 2)                          AS commitment,
    ROUND(f.drawn_amount, 2)                               AS drawn,
    f.seniority,
    ROUND(julianday(f.maturity_date) - julianday('now'), 0) AS days_to_maturity
FROM facilities f
JOIN obligors o ON f.obligor_id = o.obligor_id
WHERE f.maturity_date <= date('now', '+12 months')
  AND f.maturity_date >= date('now')
ORDER BY f.maturity_date ASC;
