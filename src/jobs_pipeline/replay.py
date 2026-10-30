# Rebuild the jobs table in the new catalog from the raw files in the bucket
import tempfile
from pathlib import Path, PurePosixPath

from . import config, lake


def main():
    con = lake.connect()
    con.execute(lake.CREATE_TABLE)

    # the path holds year/month/day, so sorting puts the oldest file first
    pattern = f"s3://{config.B2_BUCKET}/raw/jobs/**/*.parquet"
    files = sorted(row[0] for row in con.execute(f"select file from glob('{pattern}')").fetchall())
    print(f"found {len(files)} raw files")

    with tempfile.TemporaryDirectory() as tmp:
        for remote in files:
            local = Path(tmp) / PurePosixPath(remote).name

            # copy the raw file down, so your normal load() can read it
            # hive_partitioning = false keeps year/month/day out of the columns
            con.execute(
                f"copy (select * from read_parquet('{remote}', hive_partitioning = false)) "
                f"to '{local.as_posix()}' (format parquet)"
            )
            lake.load(local)

    con.close()


if __name__ == "__main__":
    main()