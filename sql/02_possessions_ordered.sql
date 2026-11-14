-- Phase 3, step 1: one row per possession, numbered in real-time order within each game.
-- File order is chronological (checked in 01_validate.sql), so file_row_number sets the order.

CREATE OR REPLACE TABLE possessions_ordered AS
SELECT
    season,
    game_id,
    period::INTEGER                                                           AS period,
    row_number() OVER (PARTITION BY game_id ORDER BY file_row_number)         AS poss_num,
    team_poss                                                                 AS team,
    opp,
    pts_poss::INTEGER                                                         AS pts
FROM possessions;