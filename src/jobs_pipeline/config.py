# Settings and secrets, all read from environment variables
import os

from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.environ["SERPAPI_KEY"]
B2_ENDPOINT = os.environ["B2_ENDPOINT"]
B2_KEY_ID = os.environ["B2_KEY_ID"]
B2_APP_KEY = os.environ["B2_APP_KEY"]
B2_BUCKET = os.environ["B2_BUCKET"]
PG_CATALOG = os.environ["PG_CATALOG"]

# What we search for
QUERY = "Data Analyst"
LOCATION = "Kenya"