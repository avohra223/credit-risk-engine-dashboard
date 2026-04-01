-- ============================================================================
-- Collateral Coverage Ratio by Facility Type
-- ============================================================================
-- Analyses the extent to which lending exposure is covered by collateral.
-- Low coverage ratios indicate higher loss severity in the event of default.
-- Useful for LGD model validation and collateral management reviews.
-- ============================================================================

SELECT
    f.facility_type,
    f.collateral_type,
    COUNT(*)                                                   AS n_facilities,
    ROUND(SUM(f.commitment_amount), 0)                         AS total_commitment,
    ROUND(SUM(f.collateral_value), 0)                          AS total_collateral,
    ROUND(
        CASE WHEN SUM(f.commitment_amount) > 0
             THEN SUM(f.collateral_value) / SUM(f.commitment_amount)
             ELSE 0
        END, 4
    )                                                          AS coverage_ratio,
    ROUND(AVG(
        CASE WHEN f.commitment_amount > 0
             THEN f.collateral_value / f.commitment_amount
             ELSE 0
        END
    ), 4)                                                      AS avg_facility_coverage
FROM facilities f
GROUP BY f.facility_type, f.collateral_type
ORDER BY f.facility_type, coverage_ratio DESC;
