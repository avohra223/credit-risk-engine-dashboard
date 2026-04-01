-- ============================================================================
-- RWA Proxy by Asset Class (Segment)
-- ============================================================================
-- Approximates risk-weighted assets by obligor segment using standardised
-- risk weights. While the Python IRB model computes exact RWA, this SQL
-- view provides a quick regulatory capital estimate for management reporting.
-- ============================================================================

SELECT
    o.segment,
    o.internal_rating,
    COUNT(f.facility_id)                                       AS n_facilities,
    ROUND(SUM(f.drawn_amount), 0)                              AS total_drawn,
    CASE o.internal_rating
        WHEN 'AAA' THEN 0.20 WHEN 'AA' THEN 0.20
        WHEN 'A' THEN 0.50 WHEN 'BBB' THEN 1.00
        WHEN 'BB' THEN 1.00 WHEN 'B' THEN 1.50
        WHEN 'CCC' THEN 1.50 WHEN 'D' THEN 1.50
    END                                                        AS sa_risk_weight,
    ROUND(SUM(f.drawn_amount) *
        CASE o.internal_rating
            WHEN 'AAA' THEN 0.20 WHEN 'AA' THEN 0.20
            WHEN 'A' THEN 0.50 WHEN 'BBB' THEN 1.00
            WHEN 'BB' THEN 1.00 WHEN 'B' THEN 1.50
            WHEN 'CCC' THEN 1.50 WHEN 'D' THEN 1.50
        END, 0)                                                AS approx_rwa
FROM obligors o
JOIN facilities f ON o.obligor_id = f.obligor_id
GROUP BY o.segment, o.internal_rating
ORDER BY o.segment, approx_rwa DESC;
