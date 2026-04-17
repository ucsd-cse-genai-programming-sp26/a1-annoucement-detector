"""
run_pipeline.py — Run the pipeline in offline batch mode.

Reads posts from data/raw_posts.jsonl (produced by scripts.fetch),
runs them through the event detection pipeline, and writes detected
events to data/detected_events.jsonl.

Usage:
    python -m scripts.run_pipeline            # process all posts
    python -m scripts.run_pipeline --limit 200  # process first N posts
"""
import sys
import os
import json
import csv
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.pipeline import EventPipeline
from monitor.filters.base import Post
from scripts.state import get_state

RAW_POSTS_PATH = "data/raw_posts.jsonl"
EVENTS_OUT     = "data/detected_events.jsonl"
STATS_LOG      = "data/pipeline_runs.csv"

PRINT_INTERVAL = 500   # print pipeline stats every N posts


def run_pipeline_batch(limit: int | None = None):
    """Process all posts in raw_posts.jsonl through the pipeline."""

    if not os.path.exists(RAW_POSTS_PATH):
        print(f"❌ No posts file found at '{RAW_POSTS_PATH}'.")
        print("   Run 'python -m scripts.fetch' first.")
        return

    pipeline = EventPipeline()
    state    = get_state()

    os.makedirs("data", exist_ok=True)

    # Count total lines for progress display
    with open(RAW_POSTS_PATH, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)

    cap = min(total_lines, limit) if limit else total_lines
    print(f"🚀 Starting batch pipeline — {cap:,} posts to process")
    print(f"   Input  : {RAW_POSTS_PATH}")
    print(f"   Output : {EVENTS_OUT}\n")

    events_found = 0

    with open(RAW_POSTS_PATH, "r", encoding="utf-8") as in_file, \
         open(EVENTS_OUT, "a", encoding="utf-8") as out_file:

        for line_num, line in enumerate(in_file, start=1):
            if limit and line_num > limit:
                break

            post_id    = None
            created_at = None

            try:
                post_data  = json.loads(line.strip())
                text       = post_data.get("record", {}).get("text", "")
                author     = post_data.get("author", {}).get("handle", "unknown")
                created_at = post_data.get("record", {}).get("createdAt", "")
                post_id    = post_data.get("uri", f"line:{line_num}")

                if not text:
                    continue

                post = Post(
                    id=post_id,
                    text=text,
                    author=author,
                    created_at=created_at,
                    raw_data=post_data,
                )

                result = pipeline.run(post)

                if result:
                    result["author"]      = author
                    result["source_text"] = text
                    result["post_id"]     = post_id
                    result["created_at"]  = created_at

                    out_file.write(json.dumps(result) + "\n")
                    out_file.flush()

                    state.increment_events()
                    events_found += 1

                    print(f"🎉 EVENT DETECTED  [{line_num:,}/{cap:,}]")
                    print(f"   Name       : {result.get('event_name', 'Unknown')}")
                    print(f"   Date       : {result.get('date', 'Unknown')}")
                    print(f"   Location   : {result.get('location', 'Unknown')}")
                    print(f"   Description: {result.get('description', 'Unknown')}")
                    print(f"   Author     : @{author}")
                    print()

                # Progress checkpoint
                if line_num % PRINT_INTERVAL == 0:
                    pct = line_num / cap * 100
                    print(f"[{line_num:,}/{cap:,} — {pct:.0f}%] pipeline stats:")
                    pipeline.print_stats()
                    print()

            except json.JSONDecodeError as e:
                print(f"⚠ Skipping malformed JSON on line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"⚠ Error on line {line_num}: {e}")
                continue

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    print("\n📊 Final Statistics:")
    pipeline.print_stats()

    stats = pipeline.get_stats_dict()
    stats["timestamp"]    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stats["events_found"] = events_found
    stats["mode"]         = "batch"
    _append_csv(STATS_LOG, stats)

    state.set_running(False)
    state.save(force=True)

    print(f"\n✅ Batch pipeline complete")
    print(f"   Events detected : {events_found:,}")
    print(f"   Events saved to : {EVENTS_OUT}")
    print(f"   Run stats saved : {STATS_LOG}")


def _append_csv(path: str, row: dict):
    """Append a row to a CSV, creating with header if the file is new."""
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Run event detection pipeline (batch mode)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max posts to process (default: all)")
    args = parser.parse_args()
    run_pipeline_batch(limit=args.limit)


if __name__ == "__main__":
    main()