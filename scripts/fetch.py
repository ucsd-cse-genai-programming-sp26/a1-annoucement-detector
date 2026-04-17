"""
fetch.py — Offline batch download from Bluesky search API.

Queries Bluesky's public search API for San Diego / California event posts.
Saves raw posts to data/raw_posts.jsonl for pipeline processing.

Usage:
    python -m scripts.fetch                  # default: 500 posts
    python -m scripts.fetch --limit 1000     # fetch up to N posts
    python -m scripts.fetch --reset          # clear state and re-fetch
"""
import json
import os
import sys
import time
import argparse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.state import get_state

# ---------------------------------------------------------------------------
# Search queries — ordered from most specific to most general.
# The fetcher runs each query and deduplicates across them.
# ---------------------------------------------------------------------------
SEARCH_QUERIES = [
    "san diego event",
    "san diego concert",
    "san diego festival",
    "san diego show",
    "san diego meetup",
    "san diego workshop",
    "san diego market",
    "sd event",
    "sdca event",
    "#sandiego event",
    "#sandiegoevent",
    "#sandiegoevents",
]

BSKY_SEARCH_URL = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"

# How many results to request per API call (max 100 per Bluesky docs)
PAGE_SIZE = 100

# Seconds to wait between API calls to avoid rate limiting
REQUEST_DELAY = 0.5

RAW_POSTS_PATH = "data/raw_posts.jsonl"


class BlueskyBatchFetcher:
    """
    Downloads posts from Bluesky search API using location-based queries.

    Features:
    - Multiple search queries with automatic deduplication
    - Cursor-based pagination through results
    - Respects configurable max-age cutoff
    - Resumable via state checkpointing
    - Rate-limit-aware request delays
    """

    def __init__(self, limit: int = 500, reset: bool = False):
        self.limit = limit
        self.state = get_state()
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "SD-Event-Monitor/1.0",
        })

        if reset:
            self.state.reset_batch()

        self._seen_uris: set[str] = set()  # in-memory dedup for this run
        self._fetched_count = 0

    def fetch_all(self) -> int:
        """
        Run all search queries and save results to raw_posts.jsonl.
        Returns total number of new posts saved.
        """
        os.makedirs("data", exist_ok=True)
        cutoff = datetime.utcnow() - timedelta(days=self.state.config["max_age_days"])

        print(f"🔍 Starting batch fetch — target: {self.limit} posts")
        print(f"   Queries  : {len(SEARCH_QUERIES)}")
        print(f"   Cutoff   : {cutoff.strftime('%Y-%m-%d')} ({self.state.config['max_age_days']} days)")
        print(f"   Output   : {RAW_POSTS_PATH}\n")

        with open(RAW_POSTS_PATH, "a", encoding="utf-8") as out_file:
            for query in SEARCH_QUERIES:
                if self._fetched_count >= self.limit:
                    break
                saved = self._fetch_query(query, cutoff, out_file)
                print(f"   ✓ '{query}': {saved} new posts")

        print(f"\n✅ Batch fetch complete — {self._fetched_count} total new posts saved")
        self.state.stats["last_fetch_count"] = self._fetched_count
        self.state.stats["last_fetch_time"] = datetime.utcnow().isoformat() + "Z"
        self.state.save(force=True)
        return self._fetched_count

    def _fetch_query(self, query: str, cutoff: datetime, out_file) -> int:
        """Paginate through all results for a single query. Returns posts saved."""
        cursor = None
        saved_this_query = 0

        while self._fetched_count < self.limit:
            params = {
                "q": query,
                "limit": min(PAGE_SIZE, self.limit - self._fetched_count),
                "sort": "latest",
            }
            if cursor:
                params["cursor"] = cursor

            try:
                resp = self.session.get(BSKY_SEARCH_URL, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.HTTPError as e:
                if resp.status_code == 429:
                    print(f"   ⚠ Rate limited — waiting 10s...")
                    time.sleep(10)
                    continue
                print(f"   ✗ HTTP error for '{query}': {e}")
                break
            except requests.exceptions.RequestException as e:
                print(f"   ✗ Request error for '{query}': {e}")
                break

            posts = data.get("posts", [])
            if not posts:
                break  # No more results

            for post in posts:
                if self._fetched_count >= self.limit:
                    break

                uri = post.get("uri", "")

                # Skip duplicates across queries
                if uri in self._seen_uris or self.state.is_duplicate(uri):
                    continue

                # Check age cutoff
                created_at_str = post.get("record", {}).get("createdAt", "")
                if created_at_str and self._is_too_old(created_at_str, cutoff):
                    continue  # Don't break — other posts in page may be newer

                # Normalise into the same shape the pipeline expects
                normalised = self._normalise(post)
                out_file.write(json.dumps(normalised) + "\n")
                out_file.flush()

                self._seen_uris.add(uri)
                self.state.mark_seen(uri)
                self._fetched_count += 1
                saved_this_query += 1

            cursor = data.get("cursor")
            if not cursor:
                break  # No more pages

            time.sleep(REQUEST_DELAY)

        return saved_this_query

    def _normalise(self, post: dict) -> dict:
        """
        Convert Bluesky search API response shape into the canonical
        post dict that the pipeline's Post object expects.
        """
        record = post.get("record", {})
        author = post.get("author", {})
        return {
            "uri": post.get("uri", ""),
            "cid": post.get("cid", ""),
            "record": {
                "text": record.get("text", ""),
                "createdAt": record.get("createdAt", ""),
                "langs": record.get("langs", []),
            },
            "author": {
                "handle": author.get("handle", "unknown"),
                "did": author.get("did", ""),
                "displayName": author.get("displayName", ""),
            },
            "indexedAt": post.get("indexedAt", ""),
            "likeCount": post.get("likeCount", 0),
            "replyCount": post.get("replyCount", 0),
            "repostCount": post.get("repostCount", 0),
            "quoteCount": post.get("quoteCount", 0),
        }

    @staticmethod
    def _is_too_old(created_at_str: str, cutoff: datetime) -> bool:
        for fmt in [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
        ]:
            try:
                dt = datetime.strptime(created_at_str, fmt)
                return dt < cutoff
            except ValueError:
                continue
        return False  # Can't parse — let it through


def fetch_posts(limit: int = 500, reset: bool = False) -> int:
    """Convenience function. Returns number of posts fetched."""
    fetcher = BlueskyBatchFetcher(limit=limit, reset=reset)
    return fetcher.fetch_all()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch-fetch San Diego event posts from Bluesky")
    parser.add_argument("--limit", type=int, default=500, help="Max posts to fetch (default: 500)")
    parser.add_argument("--reset", action="store_true", help="Clear seen-IDs state before fetching")
    args = parser.parse_args()
    fetch_posts(limit=args.limit, reset=args.reset)