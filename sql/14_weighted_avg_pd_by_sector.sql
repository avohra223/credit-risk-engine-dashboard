-- ============================================================================
-- Weighted Average PD by Sector
-- ============================================================================
-- Computes exposure-weighted average PD per sector using rating-implied
-- default probabilities. This gives a more accurate picture than simple
-- averages since larger exposures contribute more to portfolio risk.
-- ============================================================================

SELECT
    o.sector,
    COUNT(DISTINCT o.obligor_id)                               AS n_obligors,
    ROUND(SUM(f.drawn_amount), 0)                              AS total_drawn,
    ROUND(
        SUM(f.drawn_amount *
            CASE o.internal_rating
                WHEN 'AAA' THEN 0.0001 WHEN 'AA' THEN 0.0005
                WHEN 'A' THEN 0.001 WHEN 'BBB' THEN 0.0025
                WHEN 'BB' THEN 0.01 WHEN 'B' THEN 0.04
                WHEN 'CCC' THEN 0.15 WHEN 'D' THEN 1.0
            END
        ) / NULLIF(SUM(f.drawn_amount), 0),
    6)                                                         AS weighted_avg_pd,
    ROUND(
        SUM(f.drawn_amount *
            CASE o.internal_rating
                WHEN 'AAA' THEN 0.0001 WHEN 'AA' THEN 0.0005
                WHEN 'A' THEN 0.001 WHEN 'BBB' THEN 0.0025
                WHEN 'BB' THEN 0.01 WHEN 'B' THEN 0.04
                WHEN 'CCC' THEN 0.15 WHEN 'D' THEN 1.0
            END
        ) / NULLIF(SUM(f.drawn_amount), 0) * 10000,
    1)                                                         AS weighted_pd_bps
FROM obligors o
JOIN facilities f ON o.obligor_id = f.obligor_id
GROUP BY o.sector
ORDER BY weighted_avg_pd DESC;
