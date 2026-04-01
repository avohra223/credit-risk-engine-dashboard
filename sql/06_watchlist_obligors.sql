-- ============================================================================
-- Watchlist Obligors (CCC or Below)
-- ============================================================================
-- Identifies distressed or near-default obligors requiring active
-- monitoring. These names typically sit on the credit watch committee
-- agenda and may need provisioning or workout plans.
-- ============================================================================

SELECT
    o.obligor_id,
    o.obligor_name,
    o.internal_rating,
    o.sector,
    o.country,
    o.segment,
    ROUND(o.leverage_ratio, 4)                             AS leverage,
    ROUND(o.interest_coverage, 2)                          AS icr,
    ROUND(o.debt_to_ebitda, 2)                             AS debt_ebitda,
    COUNT(f.facility_id)                                   AS n_facilities,
    ROUND(SUM(f.commitment_amount), 2)                     AS total_commitment,
    ROUND(SUM(f.drawn_amount), 2)                          AS total_drawn,
    MIN(f.maturity_date)                                   AS nearest_maturity
FROM obligors o
JOIN facilities f ON o.obligor_id = f.obligor_id
WHERE o.internal_rating IN ('CCC', 'D')
   OR o.interest_coverage < 1.0
GROUP BY o.obligor_id
ORDER BY o.interest_coverage ASC;
