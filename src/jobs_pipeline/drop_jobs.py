# One-off: drop the job_listings table so the pipeline recreates it with the new columns
from . import lake


def tables(con):
    return [r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_catalog = 'lake' ORDER BY 1"
    ).fetchall()]


def main():
    con = lake.connect()
    print("tables before:", tables(con))

    if input("Type DROP to drop lake.job_listings: ").strip() != "DROP":
        print("cancelled")
    else:
        con.execute("DROP TABLE IF EXISTS lake.job_listings")
        print("tables after:", tables(con))

    con.execute("DETACH lake")
    con.close()


if __name__ == "__main__":
    main()