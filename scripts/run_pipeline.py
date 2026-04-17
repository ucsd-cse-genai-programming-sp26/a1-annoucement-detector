"""
run_pipeline.py — Run the pipeline on posts, either from file (batch) or firehose (streaming).

Usage:
    python -m scripts.run_pipeline           # Batch mode (from raw_posts.jsonl)
    python -m scripts.run_pipeline --stream  # Streaming mode (from firehose)
"""
import sys
import os
import json
import csv
import signal
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.pipeline import EventPipeline
from monitor.filters.base import Post
from scripts.fetch import FirehoseStream, fetch_bluesky
from scripts.state import get_state

RAW_PATH   = "data/raw_posts.jsonl"
EVENTS_OUT = "data/detected_events.jsonl"
STATS_LOG  = "data/pipeline_runs.csv"

# Global state for signal handling
_pipeline = None
_stream = None
_events_file = None

def _shutdown_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\n⚡ Shutdown signal received, saving results...")
    
    # Force save state
    state = get_state()
    state.save(force=True)
    
    # Close events file
    if _events_file:
        _events_file.close()
    
    sys.exit(0)

def run_pipeline_batch():
    """Run pipeline in batch mode (from existing raw_posts.jsonl)."""
    # Auto-fetch if no data exists
    if not os.path.exists(RAW_PATH):
        print("No raw data found. Fetching from BlueSky now...")
        fetch_bluesky(limit=500)

    state = get_state()

    with open(RAW_PATH, "r") as f:
        raw_posts = [json.loads(line) for line in f]

    print(f"Loaded {len(raw_posts)} posts from '{RAW_PATH}'")
    print("Running pipeline...\n")

    pipeline = EventPipeline()
    events_found = []

    for i, raw in enumerate(raw_posts):
        text       = raw.get("record", {}).get("text", "")
        author     = raw.get("author", {}).get("handle", "unknown")
        created_at = raw.get("record", {}).get("createdAt", "unknown")
        post_id    = raw.get("uri", str(i))

        if state.is_duplicate(post_id):
            continue

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
            print(f" EVENT DETECTED")
            print(f"   Name       : {result.get('event_name', 'Unknown')}")
            print(f"   Date       : {result.get('date', 'Unknown')}")
            print(f"   Location   : {result.get('location', 'Unknown')}")
            print(f"   Description: {result.get('description', 'Unknown')}")
            print(f"   Author     : @{author}")
            print()

        state.mark_processed(post_id, created_at)

    # Save detected events
    os.makedirs("data", exist_ok=True)
    with open(EVENTS_OUT, "a", encoding="utf-8") as f:
        for event in events_found:
            f.write(json.dumps(event) + "\n")

    # Persist cross-mode dedupe state
    state.save(force=True)

    print(f"Saved {len(events_found)} new events to '{EVENTS_OUT}'")
    pipeline.print_stats()

    # Save pipeline run stats to CSV
    stats = pipeline.get_stats_dict()
    stats["timestamp"]     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stats["events_found"]  = len(events_found)
    _append_csv(STATS_LOG, stats)
    print(f"Run stats saved to '{STATS_LOG}'")


def run_pipeline_stream():
    """Run pipeline in streaming mode (from firehose)."""
    global _pipeline, _stream, _events_file
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, _shutdown_handler)
    signal.signal(signal.SIGTERM, _shutdown_handler)
    
    # Initialize
    _pipeline = EventPipeline()
    state = get_state()
    
    # Open events file for appending
    os.makedirs("data", exist_ok=True)
    _events_file = open(EVENTS_OUT, "a", encoding="utf-8")
    
    print("🚀 Starting streaming pipeline...")
    print(f"   Events will be saved to: {EVENTS_OUT}")
    print("   Press Ctrl+C to stop and save\n")
    
    # Define callback for processing each post
    def process_post(post_data):
        global _pipeline, _events_file
        
        try:
            text       = post_data.get("record", {}).get("text", "")
            author     = post_data.get("author", {}).get("handle", "unknown")
            created_at = post_data.get("record", {}).get("createdAt", "unknown")
            post_id    = post_data.get("uri", str(state.stats["total_processed"]))
            
            # Skip if text is empty
            if not text:
                return True
            
            # Create Post object
            post = Post(
                id=post_id,
                text=text,
                author=author,
                created_at=created_at,
                raw_data=post_data
            )
            
            # Run through pipeline
            result = _pipeline.run(post)
            
            if result:
                result["author"]      = author
                result["source_text"] = text
                result["post_id"]     = post_id
                
                # Save event
                _events_file.write(json.dumps(result) + "\n")
                _events_file.flush()  # Ensure written to disk
                
                state.increment_events()
                
                print(f" EVENT DETECTED")
                print(f"   Name       : {result.get('event_name', 'Unknown')}")
                print(f"   Date       : {result.get('date', 'Unknown')}")
                print(f"   Location   : {result.get('location', 'Unknown')}")
                print(f"   Description: {result.get('description', 'Unknown')}")
                print(f"   Author     : @{author}")
                print()
            
            return True
            
        except Exception as e:
            print(f"Error processing post: {e}")
            return True  # Continue streaming despite errors
    
    # Create and start firehose stream
    _stream = FirehoseStream(callback=process_post)
    _stream.start()
    
    # After stream stops, print final stats
    print("\n📊 Final Statistics:")
    _pipeline.print_stats()
    
    # Save pipeline run stats to CSV
    stats = _pipeline.get_stats_dict()
    stats["timestamp"]     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stats["events_found"]  = state.stats["events_found"]
    stats["mode"]          = "streaming"
    _append_csv(STATS_LOG, stats)
    
    # Close events file
    if _events_file:
        _events_file.close()
    
    print(f"\n✅ Streaming pipeline complete")
    print(f"   Events saved to: {EVENTS_OUT}")
    print(f"   Run stats saved to: {STATS_LOG}")


def _append_csv(path, row):
    """Append a row to a CSV file, creating it if it doesn't exist."""
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Run event detection pipeline")
    parser.add_argument("--stream", action="store_true", 
                       help="Run in streaming mode (firehose)")
    parser.add_argument("--batch", action="store_true", 
                       help="Run in batch mode (from file) - default if no flag")
    
    args = parser.parse_args()
    
    if args.stream:
        run_pipeline_stream()
    else:
        run_pipeline_batch()


if __name__ == "__main__":
    main()