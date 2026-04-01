-- ============================================================================
-- Top 20 Exposures by Commitment Amount
-- ============================================================================
-- Identifies the largest single-name exposures in the portfolio.
-- Critical for monitoring concentration risk and ensuring no single
-- obligor exceeds the 5% single-name limit.
-- ============================================================================

SELECT
    o.obligor_id,
    o.obligor_name,
    o.sector,
    o.country,
    o.internal_rating,
    COUNT(f.facility_id)                                       AS n_facilities,
    ROUND(SUM(f.commitment_amount), 2)                         AS total_commitment,
    ROUND(SUM(f.drawn_amount), 2)                              AS total_drawn,
    ROUND(100.0 * SUM(f.commitment_amount) /
          (SELECT SUM(commitment_amount) FROM facilities), 2)  AS pct_of_portfolio
FROM obligors o
JOIN facilities f ON o.obligor_id = f.obligor_id
GROUP BY o.obligor_id
ORDER BY total_commitment DESC
LIMIT 20;
