-- ============================================================================
-- Portfolio Summary by Rating Grade
-- ============================================================================
-- Provides a high-level view of the lending book segmented by internal rating.
-- Risk managers use this to monitor the overall credit quality distribution
-- and flag any excessive concentration in sub-investment-grade buckets.
-- ============================================================================

SELECT
    o.internal_rating                                      AS rating,
    COUNT(DISTINCT o.obligor_id)                           AS n_obligors,
    COUNT(f.facility_id)                                   AS n_facilities,
    ROUND(SUM(f.commitment_amount), 0)                     AS total_commitment,
    ROUND(SUM(f.drawn_amount), 0)                          AS total_drawn,
    ROUND(SUM(f.commitment_amount - f.drawn_amount), 0)    AS total_undrawn,
    ROUND(AVG(o.leverage_ratio), 4)                        AS avg_leverage,
    ROUND(AVG(o.interest_coverage), 2)                     AS avg_icr,
    ROUND(AVG(o.debt_to_ebitda), 2)                        AS avg_debt_ebitda
FROM obligors o
JOIN facilities f ON o.obligor_id = f.obligor_id
GROUP BY o.internal_rating
ORDER BY
    CASE o.internal_rating
        WHEN 'AAA' THEN 1 WHEN 'AA' THEN 2 WHEN 'A' THEN 3
        WHEN 'BBB' THEN 4 WHEN 'BB' THEN 5 WHEN 'B' THEN 6
        WHEN 'CCC' THEN 7 WHEN 'D' THEN 8
    END;
