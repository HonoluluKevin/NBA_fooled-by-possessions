-- Phase 3, step 3: team-season summaries.
--   team_season_levels  one row per team-season-segment (long): the zoom curve, ready to plot/model
--   team_season         one row per team-season (wide): record, ratings, win % at every level

CREATE OR REPLACE TABLE team_season_levels AS
SELECT
    season,
    team,
    segment,
    any_value(size)                      AS size,
    count(*)                             AS units,
    count(*) FILTER (WHERE result = 'W') AS wins,
    count(*) FILTER (WHERE result = 'L') AS losses,
    count(*) FILTER (WHERE result = 'T') AS ties,
    avg(win_value)                       AS win_pct
FROM segment_results
GROUP BY season, team, segment;


CREATE OR REPLACE TABLE team_season AS
WITH

-- Ratings per 100 possessions, from the possessions table (the same points the windows use)
offense AS (
    SELECT season, team, count(*) AS off_poss, sum(pts) AS pts_scored
    FROM possessions_ordered GROUP BY season, team
),
defense AS (
    SELECT season, opp AS team, count(*) AS def_poss, sum(pts) AS pts_allowed
    FROM possessions_ordered GROUP BY season, opp
),
ratings AS (
    SELECT season, team, off_poss, def_poss,
           100.0 * pts_scored / off_poss                              AS off_rating,
           100.0 * pts_allowed / def_poss                             AS def_rating,
           100.0 * pts_scored / off_poss - 100.0 * pts_allowed / def_poss AS net_rating
    FROM offense JOIN defense USING (season, team)
),

-- Official record and point differential, from final scores
record AS (
    SELECT season, team,
           count(*)                                   AS games,
           count(*) FILTER (WHERE result = 'W')       AS wins,
           count(*) FILTER (WHERE result = 'L')       AS losses,
           avg(pts_for - pts_against)                 AS point_diff_per_game
    FROM segment_results
    WHERE segment = 'game'
    GROUP BY season, team
),

-- Win % at every level, one column per segment (win_game, win_half_1, ..., win_poss_10, ...)
win_pct_wide AS (
    PIVOT (SELECT season, team, 'win_' || segment AS col, win_pct FROM team_season_levels)
    ON col
    USING first(win_pct)
    GROUP BY season, team
)

SELECT r.season, r.team, r.games, r.wins, r.losses,
       r.point_diff_per_game,
       (t.off_poss + t.def_poss) / r.games / 2.0 AS poss_per_game,
       t.off_rating, t.def_rating, t.net_rating,
       w.* EXCLUDE (season, team)
FROM record r
JOIN ratings t USING (season, team)
JOIN win_pct_wide w USING (season, team)
ORDER BY r.season, r.team;