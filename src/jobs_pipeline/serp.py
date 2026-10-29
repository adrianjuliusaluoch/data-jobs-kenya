# Get Google Jobs listings from SerpAPI
import json
import time

import pandas as pd
from serpapi import GoogleSearch

from . import config


def as_json(value):
    # Nested fields are stored as JSON text
    return json.dumps(value) if value else None


def search_jobs(run_time):
    params = {
        "engine": "google_jobs",
        "q": config.QUERY,
        "location": config.LOCATION,
        "google_domain": "google.com",
        "hl": "en",
        "no_cache": "true",
        "api_key": config.SERPAPI_KEY,
    }
    results = GoogleSearch(params).get_dict()

    # one retry after a pause
    if "error" in results:
        print(f"Search failed: {results['error']}, retrying once...")
        time.sleep(10)
        results = GoogleSearch(params).get_dict()

    # a hard error makes the run show as failed
    if "error" in results:
        raise RuntimeError(f"Search failed again: {results['error']}")

    records = []
    for job in results.get("jobs_results", []):
        records.append({
            "title": job.get("title"),
            "company_name": job.get("company_name"),
            "location": job.get("location"),
            "via": job.get("via"),
            "description": job.get("description"),
            "job_highlights": as_json(job.get("job_highlights")),
            "extensions": as_json(job.get("extensions")),
            "detected_extensions": as_json(job.get("detected_extensions")),
            "apply_options": as_json(job.get("apply_options")),
            "job_id": job.get("job_id"),
            "scraped_at": run_time,
        })
    return pd.DataFrame(records)