"""Project settings to be altered as needed."""
from pathlib import Path

# Folders (resolved from this file, so scripts work from any directory)
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"
FIGURES_DIR = ROOT / "figures"
DB_PATH = ROOT / "data" / "nba.duckdb"

# Seasons are labelled by the year they END: 2026 = the 2025-26 season
SEASONS = list(range(2012, 2027))   # 2011-12 through 2025-26 (15 seasons)
SEASON_TYPE = "regular"
TABLES = ["pbp", "possessions"]

# Parquet files hosted at github.com/ramirobentes/nba_data, thanks ramiro
BASE_URL = "https://github.com/ramirobentes/nba_data/releases/download"

def file_name(table: str, season: int, season_type: str = SEASON_TYPE) -> str:
    """e.g. file_name('pbp', 2026) -> 'pbp_regular_2026.parquet'"""
    return f"{table}_{season_type}_{season}.parquet"

def file_url(table: str, season: int, season_type: str = SEASON_TYPE) -> str:
    return f"{BASE_URL}/{table}/{file_name(table, season, season_type)}"

# Possession windows: possessions per window, both teams combined (10 = ~5 each)
WINDOW_SIZES = [2, 4, 6, 10, 20, 30, 50, 100]

# Outputs of the transform step
TEAM_SEASON_CSV = PROCESSED_DIR / "team_season.csv"                 # one row per team-season (wide)
TEAM_SEASON_LEVELS_CSV = PROCESSED_DIR / "team_season_levels.csv"   # one row per team-season-level (long)

# Phase 4 (MVP): probability of winning at different possession scales
BEST_RECORD_SEASONS = [2022, 2023, 2024, 2025, 2026]   # team with the best record in each
EXTRA_TEAM_SEASONS = [("GSW", 2016)]                   # plus the 2016-17 Warriors (67-15)
SCALE_WINDOW_SIZES = [30, 20, 10, 6, 4, 2]             # possession rows, after game/half/quarter
SIGMA_WINDOW_SIZE = 10                                 # window size used to measure sigma
RESULTS_DIR = ROOT / "results"                         # small outputs, committed to Git