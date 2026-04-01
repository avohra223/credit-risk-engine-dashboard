-- ============================================================================
-- Geographic Distribution of Exposure
-- ============================================================================
-- Shows how the portfolio is distributed across countries. Essential for
-- sovereign and country risk monitoring, and for assessing vulnerability
-- to region-specific macroeconomic shocks.
-- ============================================================================

SELECT
    o.country,
    COUNT(DISTINCT o.obligor_id)                               AS n_obligors,
    COUNT(f.facility_id)                                       AS n_facilities,
    ROUND(SUM(f.commitment_amount), 0)                         AS total_commitment,
    ROUND(SUM(f.drawn_amount), 0)                              AS total_drawn,
    ROUND(100.0 * SUM(f.commitment_amount) /
          (SELECT SUM(commitment_amount) FROM facilities), 2)  AS pct_of_portfolio,
    f.governing_law                                            AS primary_governing_law
FROM obligors o
JOIN facilities f ON o.obligor_id = f.obligor_id
GROUP BY o.country
ORDER BY total_commitment DESC;
