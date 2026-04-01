-- ============================================================================
-- Sector Concentration Analysis
-- ============================================================================
-- Measures exposure concentration by industry sector. Used to identify
-- sector-level risk build-up and ensure the portfolio stays within
-- risk appetite limits. A single sector exceeding 20% warrants review.
-- ============================================================================

SELECT
    o.sector,
    COUNT(DISTINCT o.obligor_id)                               AS n_obligors,
    COUNT(f.facility_id)                                       AS n_facilities,
    ROUND(SUM(f.commitment_amount), 0)                         AS total_commitment,
    ROUND(SUM(f.drawn_amount), 0)                              AS total_drawn,
    ROUND(100.0 * SUM(f.commitment_amount) /
          (SELECT SUM(commitment_amount) FROM facilities), 2)  AS pct_of_portfolio,
    ROUND(AVG(o.leverage_ratio), 4)                            AS avg_leverage,
    ROUND(AVG(o.interest_coverage), 2)                         AS avg_icr
FROM obligors o
JOIN facilities f ON o.obligor_id = f.obligor_id
GROUP BY o.sector
ORDER BY total_commitment DESC;
