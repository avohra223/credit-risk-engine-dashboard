-- ============================================================================
-- Undrawn Commitment Analysis
-- ============================================================================
-- Examines off-balance sheet exposure from undrawn credit lines.
-- Revolvers and guarantees with large undrawn portions represent
-- contingent exposure that can materialise rapidly under stress.
-- ============================================================================

SELECT
    f.facility_type,
    COUNT(*)                                                   AS n_facilities,
    ROUND(SUM(f.commitment_amount), 0)                         AS total_commitment,
    ROUND(SUM(f.drawn_amount), 0)                              AS total_drawn,
    ROUND(SUM(f.undrawn_amount), 0)                            AS total_undrawn,
    ROUND(
        CASE WHEN SUM(f.commitment_amount) > 0
             THEN 100.0 * SUM(f.undrawn_amount) / SUM(f.commitment_amount)
             ELSE 0
        END, 1
    )                                                          AS undrawn_pct,
    ROUND(AVG(f.drawn_amount / f.commitment_amount), 4)        AS avg_utilisation
FROM facilities f
GROUP BY f.facility_type
ORDER BY total_undrawn DESC;
