# The lakehouse: same DuckLake as the weather pipeline, with its own table
from pathlib import Path

import duckdb

from . import config

CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS lake.job_listings (
        title VARCHAR,
        company_name VARCHAR,
        location VARCHAR,
        via VARCHAR,
        description VARCHAR,
        job_highlights VARCHAR,
        extensions VARCHAR,
        detected_extensions VARCHAR,
        apply_options VARCHAR,
        job_id VARCHAR,
        scraped_at TIMESTAMPTZ,
        source_file VARCHAR
    )
"""


def connect():
    # Open DuckDB with the bucket credentials and attach the lakehouse
    host = config.B2_ENDPOINT.replace("https://", "")
    region = host.split(".")[1]            # e.g. us-west-004

    con = duckdb.connect()
    for extension in ("ducklake", "postgres"):
        con.execute(f"INSTALL {extension}")
        con.execute(f"LOAD {extension}")
    con.execute(f"""
        CREATE OR REPLACE SECRET b2 (
            TYPE s3, KEY_ID '{config.B2_KEY_ID}', SECRET '{config.B2_APP_KEY}',
            ENDPOINT '{host}', REGION '{region}', URL_STYLE 'path'
        )
    """)

    # the data path must match the one the weather pipeline already uses
    con.execute(f"""
        ATTACH 'ducklake:postgres:{config.PG_CATALOG}' AS lake (
            DATA_PATH 's3://{config.B2_BUCKET}/lake/',
            DATA_INLINING_ROW_LIMIT 0
        )
    """)
    return con


def load(parquet_path):
    # Add one raw parquet file to the job_listings table
    name = Path(parquet_path).name
    con = connect()
    con.execute(CREATE_TABLE)

    # skip a file that was already loaded (protects against reruns)
    already = con.execute(
        "SELECT COUNT(*) FROM lake.job_listings WHERE source_file = ?", [name]
    ).fetchone()[0]
    if already:
        print(f"already loaded, skipping {name}")
    else:
        con.execute(f"""
            INSERT INTO lake.job_listings BY NAME
            SELECT *, '{name}' AS source_file
            FROM read_parquet('{Path(parquet_path).as_posix()}')
        """)
        print(f"loaded {name} into the lakehouse")

    con.execute("DETACH lake")
    con.close()