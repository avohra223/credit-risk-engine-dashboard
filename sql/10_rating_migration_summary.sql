-- ============================================================================
-- Rating Migration Summary (Current Distribution vs Implied Stress)
-- ============================================================================
-- Compares the current portfolio rating distribution against what it would
-- look like under rating downgrades. Useful for assessing the impact of
-- a broad-based 1-notch downgrade scenario on portfolio quality.
-- ============================================================================

WITH current_dist AS (
    SELECT
        internal_rating AS rating,
        COUNT(*) AS current_count,
        ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM obligors), 1) AS current_pct
    FROM obligors
    GROUP BY internal_rating
),
downgraded AS (
    SELECT
        CASE internal_rating
            WHEN 'AAA' THEN 'AA'
            WHEN 'AA' THEN 'A'
            WHEN 'A' THEN 'BBB'
            WHEN 'BBB' THEN 'BB'
            WHEN 'BB' THEN 'B'
            WHEN 'B' THEN 'CCC'
            WHEN 'CCC' THEN 'D'
            WHEN 'D' THEN 'D'
        END AS stressed_rating,
        COUNT(*) AS stressed_count
    FROM obligors
    GROUP BY stressed_rating
)
SELECT
    c.rating,
    c.current_count,
    c.current_pct,
    COALESCE(d.stressed_count, 0) AS after_1notch_downgrade,
    ROUND(COALESCE(d.stressed_count, 0) * 100.0 / (SELECT COUNT(*) FROM obligors), 1) AS stressed_pct
FROM current_dist c
LEFT JOIN downgraded d ON c.rating = d.stressed_rating
ORDER BY
    CASE c.rating
        WHEN 'AAA' THEN 1 WHEN 'AA' THEN 2 WHEN 'A' THEN 3
        WHEN 'BBB' THEN 4 WHEN 'BB' THEN 5 WHEN 'B' THEN 6
        WHEN 'CCC' THEN 7 WHEN 'D' THEN 8
    END;
