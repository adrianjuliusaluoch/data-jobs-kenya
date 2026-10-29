# Get Google Jobs listings from SerpAPI, one page at a time
import json
import time

import pandas as pd
from serpapi import GoogleSearch

from . import config


def as_json(value):
    # nested fields are stored as JSON text
    return json.dumps(value) if value else None


def get_page(params, retry):
    # one search; only the first page is retried, because on later pages an error just means the end
    results = GoogleSearch(params).get_dict()
    if "error" in results and retry:
        print(f"Search failed: {results['error']}, retrying once...")
        time.sleep(10)
        results = GoogleSearch(params).get_dict()
    return results


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

    records = []
    for page in range(1, config.max_pages + 1):
        results = get_page(params, retry=(page == 1))

        if "error" in results:
            if page == 1:
                # a hard error on the first page makes the run show as failed
                raise RuntimeError(f"Search failed: {results['error']}")
            print(f"page {page}: {results['error']}, treating it as the last page")
            break

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
        print(f"page {page}: {len(results.get('jobs_results', []))} listings")

        # no token means that was the last page
        token = results.get("serpapi_pagination", {}).get("next_page_token")
        if not token:
            break
        params["next_page_token"] = token
        time.sleep(1)

    # the same job can appear on two pages, keep one copy per run
    return pd.DataFrame(records).drop_duplicates(subset="job_id")