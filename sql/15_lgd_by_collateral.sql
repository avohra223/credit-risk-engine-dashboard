-- ============================================================================
-- LGD Distribution by Collateral Type
-- ============================================================================
-- Analyses the portfolio's collateral composition and implied loss severity.
-- Higher collateral coverage reduces LGD; unsecured exposures carry the
-- highest loss given default. Used for LGD model benchmarking and
-- collateral policy reviews.
-- ============================================================================

SELECT
    f.collateral_type,
    f.seniority,
    COUNT(*)                                                   AS n_facilities,
    ROUND(SUM(f.commitment_amount), 0)                         AS total_commitment,
    ROUND(SUM(f.collateral_value), 0)                          AS total_collateral,
    ROUND(
        AVG(CASE WHEN f.commitment_amount > 0
            THEN f.collateral_value / f.commitment_amount
            ELSE 0 END
        ), 4
    )                                                          AS avg_coverage_ratio,
    CASE f.collateral_type
        WHEN 'real_estate' THEN 0.30
        WHEN 'equipment' THEN 0.50
        WHEN 'financial_assets' THEN 0.15
        WHEN 'unsecured' THEN 1.00
    END                                                        AS haircut,
    CASE f.seniority
        WHEN 'senior_secured' THEN 0.25
        WHEN 'senior_unsecured' THEN 0.45
        WHEN 'subordinated' THEN 0.70
    END                                                        AS base_lgd
FROM facilities f
GROUP BY f.collateral_type, f.seniority
ORDER BY base_lgd ASC, avg_coverage_ratio DESC;
