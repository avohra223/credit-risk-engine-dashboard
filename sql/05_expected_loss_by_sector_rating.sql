-- ============================================================================
-- Expected Loss Proxy by Sector and Rating
-- ============================================================================
-- Approximates expected loss using drawn exposure and rating-implied PD.
-- This SQL-level approximation complements the Python model output and
-- is useful for quick portfolio-level EL estimation without running models.
-- ============================================================================

SELECT
    o.sector,
    o.internal_rating                                          AS rating,
    COUNT(f.facility_id)                                       AS n_facilities,
    ROUND(SUM(f.drawn_amount), 0)                              AS total_drawn,
    ROUND(AVG(
        CASE o.internal_rating
            WHEN 'AAA' THEN 0.0001 WHEN 'AA' THEN 0.0005
            WHEN 'A' THEN 0.001 WHEN 'BBB' THEN 0.0025
            WHEN 'BB' THEN 0.01 WHEN 'B' THEN 0.04
            WHEN 'CCC' THEN 0.15 WHEN 'D' THEN 1.0
        END
    ), 6)                                                      AS avg_pd,
    ROUND(SUM(f.drawn_amount) *
        CASE o.internal_rating
            WHEN 'AAA' THEN 0.0001 WHEN 'AA' THEN 0.0005
            WHEN 'A' THEN 0.001 WHEN 'BBB' THEN 0.0025
            WHEN 'BB' THEN 0.01 WHEN 'B' THEN 0.04
            WHEN 'CCC' THEN 0.15 WHEN 'D' THEN 1.0
        END * 0.45, 2)                                         AS approx_el
FROM obligors o
JOIN facilities f ON o.obligor_id = f.obligor_id
GROUP BY o.sector, o.internal_rating
ORDER BY o.sector, approx_el DESC;
