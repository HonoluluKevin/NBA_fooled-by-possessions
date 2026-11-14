"""Phase 3: build the analysis tables in data/nba.duckdb and export the team-season tables."""
from src import config
from src.db import connect

SQL_STEPS = [
    "02_possessions_ordered.sql",   # possessions numbered in real-time order
    "03_segment_results.sql",       # team x game x segment results (game, halves, quarters, windows)
    "04_team_season.sql",           # team-season summaries (long and wide)
]


def run_transform():
    con = connect(config.DB_PATH)

    # Window sizes from config.py, as a one-column table the SQL can join to
    con.execute("CREATE OR REPLACE TABLE window_sizes (size INTEGER)")
    con.executemany("INSERT INTO window_sizes VALUES (?)", [(s,) for s in config.WINDOW_SIZES])

    for step in SQL_STEPS:
        con.execute((config.SQL_DIR / step).read_text())
        print(f"  ran {step}")

    for table in ["possessions_ordered", "segment_results", "team_season_levels", "team_season"]:
        n = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"  {table:<20} {n:>12,} rows")

    # Export, with win % columns ordered from the whole game down to the smallest window
    team_season = con.execute("SELECT * FROM team_season").df()
    win_cols = (["win_game", "win_half_1", "win_half_2", "win_quarter"]
                + [f"win_poss_{s}" for s in sorted(config.WINDOW_SIZES, reverse=True)])
    other_cols = [c for c in team_season.columns if not c.startswith("win_")]
    team_season = team_season[other_cols + win_cols]
    team_season.to_csv(config.TEAM_SEASON_CSV, index=False)

    levels = con.execute("SELECT * FROM team_season_levels ORDER BY season, team, segment").df()
    levels.to_csv(config.TEAM_SEASON_LEVELS_CSV, index=False)

    # Every team-season should have a value for every level; a gap means a join went wrong
    gaps = team_season[team_season[win_cols + ["net_rating"]].isna().any(axis=1)]
    if len(gaps):
        print(f"WARNING: {len(gaps)} team-seasons have missing values:\n{gaps[['season', 'team']]}")

    print(f"  saved {config.TEAM_SEASON_CSV.name} and {config.TEAM_SEASON_LEVELS_CSV.name}")
    con.close()
    return team_season