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