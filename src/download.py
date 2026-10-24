"""Phase 2a: download the raw Parquet files into data/raw/.

Files already on disk are skipped, so re-running is cheap. Each file is
written to a temporary name first and renamed only when complete, so an
interrupted download never leaves a half-written file behind.
"""
import requests

from src import config


def download_file(url, dest):
    tmp = dest.with_suffix(".part")
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()           # stop on 404 etc. instead of saving an error page
        with open(tmp, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    tmp.rename(dest)


def download_all():
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    jobs = [(table, season) for table in config.TABLES for season in config.SEASONS]
    for i, (table, season) in enumerate(jobs, start=1):
        dest = config.RAW_DIR / config.file_name(table, season)
        label = f"[{i}/{len(jobs)}] {dest.name}"
        if dest.exists():
            print(f"{label}  already downloaded")
            continue
        download_file(config.file_url(table, season), dest)
        print(f"{label}  {dest.stat().st_size / 1e6:.1f} MB")