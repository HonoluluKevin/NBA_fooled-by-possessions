-- Phase 3, step 2: one row per team x game x segment, with points for/against and the result.
--
-- Segments:
--   game     final score, including overtime                      (from play-by-play)
--   half_1/2 points scored WITHIN each half, regulation only       (from play-by-play)
--   quarter  points scored WITHIN each quarter, regulation only    (from play-by-play)
--   poss_N   disjoint windows of N possessions (both teams), counted continuously through
--            quarter breaks and overtime; a partial window at the end of a game is dropped
--                                                                  (from possessions_ordered)
-- A tie is worth half a win (win_value = 0.5).

CREATE OR REPLACE TABLE segment_results AS
WITH

-- ---- Games, halves, quarters (play-by-play) -------------------------------------------

-- Score at the end of each period (msg_type 13 = "End Period"); one row per game-period
period_ends AS (
    SELECT season, game_id, team_home, team_away, period::INTEGER AS period,
           hs::INTEGER AS hs, vs::INTEGER AS vs
    FROM pbp
    WHERE msg_type = 13
    QUALIFY row_number() OVER (PARTITION BY game_id, period ORDER BY hs + vs DESC) = 1
),

-- Points scored WITHIN each period = change in score since the previous period ended
period_points AS (
    SELECT *,
           hs - coalesce(lag(hs) OVER w, 0) AS home_pts,
           vs - coalesce(lag(vs) OVER w, 0) AS away_pts
    FROM period_ends
    WINDOW w AS (PARTITION BY game_id ORDER BY period)
),

finals AS (
    SELECT season, game_id, team_home, team_away, hs AS home_pts, vs AS away_pts
    FROM period_ends
    QUALIFY row_number() OVER (PARTITION BY game_id ORDER BY period DESC) = 1
),

-- Every game-level segment, from the home team's point of view
home_view AS (
    SELECT season, game_id, team_home, team_away,
           'game' AS segment, NULL::INTEGER AS size, 1 AS unit, home_pts, away_pts
    FROM finals

    UNION ALL
    SELECT season, game_id, team_home, team_away,
           'half_' || ((period + 1) // 2), NULL, (period + 1) // 2, sum(home_pts), sum(away_pts)
    FROM period_points
    WHERE period <= 4
    GROUP BY ALL

    UNION ALL
    SELECT season, game_id, team_home, team_away,
           'quarter', NULL, period, home_pts, away_pts
    FROM period_points
    WHERE period <= 4
),

-- Two rows per segment: one for each team
period_segments AS (
    SELECT season, game_id, segment, size, unit,
           team_home AS team, team_away AS opp, home_pts AS pts_for, away_pts AS pts_against
    FROM home_view
    UNION ALL
    SELECT season, game_id, segment, size, unit,
           team_away, team_home, away_pts, home_pts
    FROM home_view
),

-- ---- Possession windows (possessions table) ---------------------------------------------

-- Each possession assigned to a window, once per window size (window_sizes comes from config.py)
windows AS (
    SELECT p.season, p.game_id, w.size,
           (p.poss_num - 1) // w.size + 1 AS unit,
           p.team, p.opp, p.pts
    FROM possessions_ordered p
    CROSS JOIN window_sizes w
    QUALIFY count(*) OVER (PARTITION BY p.game_id, w.size, unit) = w.size   -- drop partial windows
),

-- A possession's points count FOR the team with the ball and AGAINST its opponent
window_segments AS (
    SELECT season, game_id, 'poss_' || size AS segment, size, unit,
           team, opp, sum(pts_for)::INTEGER AS pts_for, sum(pts_against)::INTEGER AS pts_against
    FROM (
        SELECT season, game_id, size, unit, team, opp, pts AS pts_for, 0 AS pts_against FROM windows
        UNION ALL
        SELECT season, game_id, size, unit, opp, team, 0, pts FROM windows
    )
    GROUP BY ALL
)

-- ---- Combine and score ---------------------------------------------------------------------

SELECT *,
       CASE WHEN pts_for > pts_against THEN 'W'
            WHEN pts_for < pts_against THEN 'L'
            ELSE 'T' END                                   AS result,
       CASE WHEN pts_for > pts_against THEN 1.0
            WHEN pts_for < pts_against THEN 0.0
            ELSE 0.5 END                                   AS win_value
FROM (
    SELECT * FROM period_segments
    UNION ALL
    SELECT * FROM window_segments
);