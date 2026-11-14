-- Reads the views `pbp` and `possessions` (see src/db.py).

WITH
-- Final score of each game = the score on its last "End Period" event (msg_type 13)
finals AS (
    SELECT season, game_id, hs + vs AS final_total
    FROM pbp
    WHERE msg_type = 13
    QUALIFY row_number() OVER (PARTITION BY game_id ORDER BY period DESC, hs + vs DESC) = 1
),

-- Games where at least one of the four regulation quarters has no end-of-period row
missing_quarters AS (
    SELECT game_id
    FROM pbp
    WHERE msg_type = 13 AND period <= 4
    GROUP BY game_id
    HAVING count(DISTINCT period) < 4
),

-- Points and possession counts per game, from the possessions table
poss_totals AS (
    SELECT game_id, sum(pts_poss) AS poss_total, count(*) AS n_poss
    FROM possessions
    GROUP BY game_id
),

-- Games whose possessions, in file order, ever step back to an earlier period.
-- Phase 3 relies on file order being real-time order, so this should always be empty.
out_of_order AS (
    SELECT DISTINCT game_id
    FROM (
        SELECT game_id, period,
               lag(period) OVER (PARTITION BY game_id ORDER BY file_row_number) AS prev_period
        FROM possessions
    )
    WHERE period < prev_period
)

SELECT
    f.season,
    count(*)                                                      AS games,
    count(m.game_id)                                              AS games_missing_quarter_ends,
    count(*) - count(p.game_id)                                   AS games_missing_possessions,
    count(o.game_id)                                              AS games_possessions_out_of_order,
    round(avg(p.n_poss), 1)                                       AS avg_possessions_per_game,
    round(100 * avg((p.poss_total <> f.final_total)::int), 1)     AS pct_games_points_mismatch,
    max(f.final_total - p.poss_total)                             AS max_points_missing
FROM finals f
LEFT JOIN missing_quarters m USING (game_id)
LEFT JOIN poss_totals p USING (game_id)
LEFT JOIN out_of_order o USING (game_id)
GROUP BY f.season
ORDER BY f.season;