"""Shared DuckDB connection: exposes the raw Parquet files as two SQL views."""
import duckdb

from src import config


def connect(database=":memory:"):
    """Open DuckDB (in memory by default, or a database file) with views `pbp` and `possessions`.

    Each view stacks all seasons' files into one table. `possessions` also carries
    `file_row_number`, each row's position in its file, which records the real-time
    order of possessions (SQL tables have no built-in row order).
    """
    con = duckdb.connect(str(database))
    pbp_files = (config.RAW_DIR / f"pbp_{config.SEASON_TYPE}_*.parquet").as_posix()
    poss_files = (config.RAW_DIR / f"possessions_{config.SEASON_TYPE}_*.parquet").as_posix()
    con.execute(f"CREATE OR REPLACE VIEW pbp AS SELECT * FROM read_parquet('{pbp_files}')")
    con.execute(f"""CREATE OR REPLACE VIEW possessions AS
                    SELECT * FROM read_parquet('{poss_files}', file_row_number = true)""")
    return con