"""Phase 2b: run sanity checks on the raw files and save a per-season report."""
import duckdb

from src import config

# Regular-season games per season; short seasons are expected, anything else is a red flag
EXPECTED_GAMES = {
    2012: 990,    # 2011-12 lockout: 66 games per team
    2013: 1229,   # Celtics-Pacers game cancelled after the Boston Marathon bombing, never made up
    2020: 1059,   # 2019-20 COVID: 971 games before the suspension + 88 bubble seeding games
    2021: 1080,   # 2020-21: 72 games per team
}
DEFAULT_GAMES = 1230


def connect():
    """In-memory DuckDB connection with one view per raw table (all seasons stacked)."""
    con = duckdb.connect()
    for table in config.TABLES:
        files = (config.RAW_DIR / f"{table}_{config.SEASON_TYPE}_*.parquet").as_posix()
        con.execute(f"CREATE VIEW {table} AS SELECT * FROM read_parquet('{files}')")
    return con


def run_validation():
    con = connect()
    query = (config.SQL_DIR / "01_validate.sql").read_text()
    report = con.execute(query).df()

    report["expected_games"] = report["season"].map(EXPECTED_GAMES).fillna(DEFAULT_GAMES).astype(int)
    report["ok"] = (
        (report["games"] == report["expected_games"])
        & (report["games_missing_quarter_ends"] == 0)
        & (report["games_missing_possessions"] == 0)
    )

    out = config.PROCESSED_DIR / "validation_report.csv"
    report.to_csv(out, index=False)
    print(report.to_string(index=False))
    print(f"\nSaved to {out}")
    if not report["ok"].all():
        print("WARNING: some seasons failed a check (see the 'ok' column).")
    return report