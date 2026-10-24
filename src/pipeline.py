"""Runs the whole project in order. From the project folder:  python -m src.pipeline"""
from src import config
from src.download import download_all
from src.validate import run_validation


def download():
    """Phase 2: fetch play-by-play and possessions Parquet files into data/raw/."""
    print("[download]")
    download_all()


def validate():
    """Phase 2: sanity checks (games per season, possession points vs. final score)."""
    print("\n[validate]")
    run_validation()


def transform():
    """Phase 3: run the SQL in sql/ to build windows and team-season tables."""
    print(f"\n[transform] TODO: SQL files in {config.SQL_DIR}")


def main():
    for folder in (config.RAW_DIR, config.PROCESSED_DIR, config.FIGURES_DIR):
        folder.mkdir(parents=True, exist_ok=True)
    download()
    validate()
    transform()
    print("\nPipeline finished.")


if __name__ == "__main__":
    main()