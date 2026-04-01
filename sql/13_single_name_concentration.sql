-- ============================================================================
-- Single-Name Concentration Breaches (>5% of Portfolio)
-- ============================================================================
-- Flags obligors whose total exposure exceeds the 5% single-name limit.
-- Concentration risk is a key supervisory focus under Pillar 2; breaches
-- require immediate attention and a remediation plan.
-- ============================================================================

WITH portfolio_total AS (
    SELECT SUM(commitment_amount) AS total FROM facilities
),
obligor_exposure AS (
    SELECT
        o.obligor_id,
        o.obligor_name,
        o.sector,
        o.country,
        o.internal_rating,
        SUM(f.commitment_amount) AS total_exposure
    FROM obligors o
    JOIN facilities f ON o.obligor_id = f.obligor_id
    GROUP BY o.obligor_id
)
SELECT
    oe.obligor_id,
    oe.obligor_name,
    oe.sector,
    oe.country,
    oe.internal_rating,
    ROUND(oe.total_exposure, 2)                            AS total_exposure,
    ROUND(100.0 * oe.total_exposure / pt.total, 2)        AS pct_of_portfolio,
    CASE
        WHEN oe.total_exposure / pt.total > 0.05 THEN 'BREACH'
        WHEN oe.total_exposure / pt.total > 0.04 THEN 'WARNING'
        ELSE 'OK'
    END                                                    AS status
FROM obligor_exposure oe
CROSS JOIN portfolio_total pt
WHERE oe.total_exposure / pt.total > 0.03
ORDER BY pct_of_portfolio DESC;
