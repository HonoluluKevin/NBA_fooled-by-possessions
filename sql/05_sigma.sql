-- Phase 4: how much does the scoring margin bounce around, per possession?
--
-- For each window size, take every window's margin, subtract what the two teams' net ratings
-- predict for it, and measure the variance of what's left. Dividing by the window size gives
-- the variance PER POSSESSION. If possessions were independent coin flips, this would be the
-- same at every size; where it changes, the simple random-walk model stops applying.

WITH windows AS (
    SELECT
        r.size,
        r.pts_for - r.pts_against                              AS margin,
        r.size * (a.net_rating - b.net_rating) / 200           AS expected_margin
    FROM segment_results r
    JOIN team_season a ON a.season = r.season AND a.team = r.team
    JOIN team_season b ON b.season = r.season AND b.team = r.opp
    WHERE r.size IS NOT NULL          -- possession windows only
      AND r.team < r.opp              -- each window appears twice (once per team); keep one
)
SELECT
    size,
    count(*)                                             AS windows,
    var_samp(margin - expected_margin) / size            AS var_per_possession,
    sqrt(var_samp(margin - expected_margin) / size)      AS sigma
FROM windows
GROUP BY size
ORDER BY size;