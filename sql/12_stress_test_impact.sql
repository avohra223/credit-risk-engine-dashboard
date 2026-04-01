-- ============================================================================
-- Stress Test Impact Comparison (Sector Vulnerability)
-- ============================================================================
-- Identifies which sectors are most vulnerable to macroeconomic stress
-- by combining current credit quality metrics with sector risk sensitivity.
-- Higher-leverage, lower-ICR sectors with cyclical exposure face the
-- greatest PD deterioration under adverse conditions.
-- ============================================================================

SELECT
    o.sector,
    COUNT(DISTINCT o.obligor_id)                           AS n_obligors,
    ROUND(AVG(o.leverage_ratio), 4)                        AS avg_leverage,
    ROUND(AVG(o.interest_coverage), 2)                     AS avg_icr,
    ROUND(AVG(o.debt_to_ebitda), 2)                        AS avg_debt_ebitda,
    SUM(CASE WHEN o.internal_rating IN ('B', 'CCC', 'D') THEN 1 ELSE 0 END) AS sub_ig_count,
    ROUND(100.0 * SUM(CASE WHEN o.internal_rating IN ('B', 'CCC', 'D') THEN 1 ELSE 0 END) /
          COUNT(*), 1)                                     AS sub_ig_pct,
    ROUND(SUM(f.drawn_amount), 0)                          AS total_drawn,
    CASE
        WHEN AVG(o.interest_coverage) < 2.0 THEN 'HIGH'
        WHEN AVG(o.interest_coverage) < 4.0 THEN 'MEDIUM'
        ELSE 'LOW'
    END                                                    AS stress_vulnerability
FROM obligors o
JOIN facilities f ON o.obligor_id = f.obligor_id
GROUP BY o.sector
ORDER BY avg_icr ASC;
