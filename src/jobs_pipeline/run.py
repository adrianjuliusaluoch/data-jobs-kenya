# The pipeline: search for jobs, save the raw file, add it to the lakehouse
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import lake, serp, storage


def main():
    run_time = datetime.now(timezone.utc)

    jobs = serp.search_jobs(run_time)
    if jobs.empty:
        print("No job listings this run, nothing to load.")
        return
    print(f"got {len(jobs)} job listings")

    # raw layer: one parquet file per run, in date folders
    name = f"jobs_{run_time:%Y%m%dT%H%M%SZ}.parquet"
    key = f"raw/jobs/year={run_time:%Y}/month={run_time:%m}/day={run_time:%d}/{name}"

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        jobs.to_parquet(path, index=False)
        storage.upload(path, key)
        print(f"uploaded {key}")

        # lakehouse layer: the same file goes into the table
        lake.load(path)


if __name__ == "__main__":
    main()