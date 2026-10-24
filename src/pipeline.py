"""Runs the whole project in order. From the project folder:  python -m src.pipeline"""
from src import config


def download():
    """Phase 2: fetch play-by-play and possessions Parquet files into data/raw/."""
    print(f"[download]  TODO: {len(config.TABLES) * len(config.SEASONS)} files "
          f"({config.SEASONS[0]}-{config.SEASONS[-1]}) -> {config.RAW_DIR}")


def validate():
    """Phase 2: sanity checks (games per season, possession points vs. final score)."""
    print("[validate]  TODO")


def transform():
    """Phase 3: run the SQL in sql/ to build windows and team-season tables."""
    print(f"[transform] TODO: SQL files in {config.SQL_DIR}")


def main():
    for folder in (config.RAW_DIR, config.PROCESSED_DIR, config.FIGURES_DIR):
        folder.mkdir(parents=True, exist_ok=True)
    download()
    validate()
    transform()
    print("Pipeline finished.")


if __name__ == "__main__":
    main()