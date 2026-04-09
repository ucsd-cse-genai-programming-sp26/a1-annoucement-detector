"""
run_pipeline.py — run the pipeline on all raw posts and save detected events.

Usage:
    python -m scripts.run_pipeline
"""
import sys
import os
import json
import csv
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.pipeline import EventPipeline
from monitor.filters.base import Post

RAW_PATH   = "data/raw_posts.jsonl"
EVENTS_OUT = "data/detected_events.jsonl"
STATS_LOG  = "data/pipeline_runs.csv"   # one row per pipeline run

def run_pipeline():
    # Auto-fetch if no data exists
    if not os.path.exists(RAW_PATH):
        print("No raw data found. Fetching from BlueSky now...")
        from scripts.fetch import fetch_bluesky
        fetch_bluesky(query="San Diego", limit=500)

    with open(RAW_PATH, "r") as f:
        raw_posts = [json.loads(line) for line in f]

    print(f"Loaded {len(raw_posts)} posts from '{RAW_PATH}'")
    print("Running pipeline...\n")

    pipeline     = EventPipeline()
    events_found = []

    for i, raw in enumerate(raw_posts):
        text       = raw.get("record", {}).get("text", "")
        author     = raw.get("author", {}).get("handle", "unknown")
        created_at = raw.get("record", {}).get("createdAt", "unknown")
        post_id    = raw.get("uri", str(i))

        post = Post(
            id=post_id,
            text=text,
            author=author,
            created_at=created_at,
            raw_data=raw
        )

        result = pipeline.run(post)

        if result:
            result["author"]      = author
            result["source_text"] = text
            result["post_id"]     = post_id
            events_found.append(result)
            print(f"✅ EVENT DETECTED")
            print(f"   Name       : {result.get('event_name', 'Unknown')}")
            print(f"   Date       : {result.get('date', 'Unknown')}")
            print(f"   Location   : {result.get('location', 'Unknown')}")
            print(f"   Description: {result.get('description', 'Unknown')}")
            print(f"   Author     : @{author}")
            print()

    # Save detected events
    os.makedirs("data", exist_ok=True)
    with open(EVENTS_OUT, "w", encoding="utf-8") as f:
        for event in events_found:
            f.write(json.dumps(event) + "\n")

    print(f"Saved {len(events_found)} events to '{EVENTS_OUT}'")
    pipeline.print_stats()

    # Save pipeline run stats to CSV
    stats = pipeline.get_stats_dict()
    stats["timestamp"]     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stats["events_found"]  = len(events_found)
    _append_csv(STATS_LOG, stats)
    print(f"Run stats saved to '{STATS_LOG}'")


def _append_csv(path, row):
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


if __name__ == "__main__":
    run_pipeline()