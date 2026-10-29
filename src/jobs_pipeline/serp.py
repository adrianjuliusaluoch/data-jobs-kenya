# Get Google Jobs listings from SerpAPI, one job title at a time
import json
import time

import pandas as pd
from serpapi import GoogleSearch

from . import config


def as_json(value):
    # nested fields are stored as JSON text
    return json.dumps(value) if value else None


def get_page(params):
    # one search; retry once on an error, unless it just says the page is empty
    results = GoogleSearch(params).get_dict()
    error = results.get("error")
    if error and "any results" not in error:
        print(f"  search failed: {error}, retrying once...")
        time.sleep(10)
        results = GoogleSearch(params).get_dict()
    return results


def search_one(query, run_time):
    # all pages (up to max_pages) for one job title
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": config.LOCATION,
        "google_domain": "google.com",
        "hl": "en",
        "api_key": config.SERPAPI_KEY,
    }

    records = []
    for page in range(1, config.max_pages + 1):
        results = get_page(params)

        if "error" in results:
            if page == 1:
                raise RuntimeError(results["error"])
            print(f"  {query} page {page}: stopped, {results['error']}")
            break

        jobs = results.get("jobs_results", [])
        status = results.get("search_metadata", {}).get("status")
        print(f"  {query} page {page}: {len(jobs)} listings ({status})")

        for job in jobs:
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
                "search_query": query,
                "scraped_at": run_time,
            })

        # no token means that was the last page
        token = results.get("serpapi_pagination", {}).get("next_page_token")
        if not token:
            print(f"  {query}: no next page token after page {page}")
            break
        params["next_page_token"] = token
        time.sleep(1)

    return records


def search_jobs(run_time):
    records, failed = [], []
    for query in config.queries:
        try:
            found = search_one(query, run_time)
        except RuntimeError as e:
            print(f"{query}: failed ({e})")
            failed.append(query)
            continue
        print(f"{query}: {len(found)} listings total")
        records.extend(found)
        time.sleep(1)

    # if every title failed, make the run show as failed
    if len(failed) == len(config.queries):
        raise RuntimeError("every search failed")
    if failed:
        print(f"warning: these searches failed and were skipped: {failed}")
    if not records:
        return pd.DataFrame()

    # one copy per run: first by job_id, then by the same key the old script used
    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset="job_id")
    df = df.drop_duplicates(subset=["title", "description", "company_name", "via"])
    return df