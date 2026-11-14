-- Phase 4: win % at every level for the featured team-seasons.
-- Featured = the best record in each season listed in $best_seasons (ties broken by net
-- rating), plus any team-seasons in `extra_teams` (registered from Python).

WITH best AS (
    SELECT season, team
    FROM team_season
    WHERE list_contains($best_seasons, season)
    QUALIFY row_number() OVER (PARTITION BY season ORDER BY wins DESC, net_rating DESC) = 1
),
featured AS (
    SELECT season, team FROM best
    UNION
    SELECT season, team FROM extra_teams
)
SELECT t.season, t.team, t.wins, t.losses, t.net_rating, t.poss_per_game,
       l.segment, l.win_pct
FROM featured f
JOIN team_season t USING (season, team)
JOIN team_season_levels l USING (season, team)
ORDER BY t.season DESC, t.team;