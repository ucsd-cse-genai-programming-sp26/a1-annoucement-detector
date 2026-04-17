"""
state.py — State management for batch and streaming modes.

Handles persistence of processing state:
- Seen post URIs for deduplication (bounded, no memory leak)
- Processing statistics
- Batch fetch tracking
"""
import json
import os
from datetime import datetime, timedelta
from collections import deque

STATE_PATH = "data/state.json"

# Maximum number of post URIs to remember for deduplication.
# At ~60 bytes per URI this is ~6 MB worst-case — safe for long runs.
MAX_SEEN_IDS = 100_000


class StreamState:
    """Manages processing state for resumable batch and streaming runs."""

    def __init__(self, state_path: str = STATE_PATH):
        self.state_path = state_path

        # Bounded deque — automatically evicts oldest IDs when full.
        # Used for both deduplication AND persistence. No unbounded set.
        self._seen_ids: deque = deque(maxlen=MAX_SEEN_IDS)
        self._seen_ids_set: set = set()   # mirror set for O(1) lookup

        self.last_timestamp = None
        self.stats = {
            "total_processed": 0,
            "events_found": 0,
            "last_run": None,
            "start_time": None,
            "last_fetch_count": 0,
            "last_fetch_time": None,
        }
        self.config = {
            "max_age_days": 60,
            "seen_ids_limit": MAX_SEEN_IDS,
            "save_interval_posts": 100,
            "save_interval_seconds": 30,
        }
        self._posts_since_save = 0
        self._last_save_time = datetime.utcnow()

        self.load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self):
        """Load state from file if it exists."""
        if not os.path.exists(self.state_path):
            return

        try:
            with open(self.state_path, "r") as f:
                data = json.load(f)

            self.last_timestamp = data.get("last_timestamp")

            seen_ids = data.get("seen_ids", [])
            limit = self.config["seen_ids_limit"]
            # Only keep the most recent N IDs to respect the cap
            self._seen_ids = deque(seen_ids[-limit:], maxlen=limit)
            self._seen_ids_set = set(self._seen_ids)

            saved_stats = data.get("stats", {})
            self.stats.update(saved_stats)

            saved_config = data.get("config", {})
            self.config.update(saved_config)

            print(f"📂 Loaded state from {self.state_path}")
            print(f"   Seen IDs        : {len(self._seen_ids):,}")
            print(f"   Total processed : {self.stats['total_processed']:,}")
            if self.stats.get("last_fetch_time"):
                print(f"   Last fetch      : {self.stats['last_fetch_time']}")

        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠ Could not load state file: {e} — starting fresh.")

    def save(self, force: bool = False) -> bool:
        """Save state to file. Force save ignores interval checks."""
        should_save = force

        if not should_save:
            should_save = self._posts_since_save >= self.config["save_interval_posts"]

        if not should_save:
            elapsed = (datetime.utcnow() - self._last_save_time).total_seconds()
            should_save = elapsed >= self.config["save_interval_seconds"]

        if not should_save:
            return False

        try:
            os.makedirs(os.path.dirname(self.state_path) or ".", exist_ok=True)

            data = {
                "last_timestamp": self.last_timestamp,
                "seen_ids": list(self._seen_ids),
                "stats": self.stats,
                "config": self.config,
            }

            temp_path = self.state_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)

            # Atomic rename
            if os.path.exists(self.state_path):
                os.remove(self.state_path)
            os.rename(temp_path, self.state_path)

            self._posts_since_save = 0
            self._last_save_time = datetime.utcnow()

            if force:
                print(f"💾 State saved to {self.state_path}")

            return True

        except Exception as e:
            print(f"❌ Error saving state: {e}")
            return False

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------

    def is_duplicate(self, post_id: str) -> bool:
        """O(1) duplicate check using the mirror set."""
        return post_id in self._seen_ids_set

    def mark_seen(self, post_id: str):
        """
        Mark a post ID as seen. Maintains both the bounded deque and its
        mirror set. When the deque evicts an old ID, we rebuild the set
        to stay consistent. Rebuilds are O(N) but only happen when the
        deque is full, amortising the cost.
        """
        if post_id in self._seen_ids_set:
            return

        was_full = len(self._seen_ids) == self._seen_ids.maxlen
        self._seen_ids.append(post_id)

        if was_full:
            # An old entry was evicted — rebuild mirror set from scratch
            self._seen_ids_set = set(self._seen_ids)
        else:
            self._seen_ids_set.add(post_id)

    def mark_processed(self, post_id: str | None, timestamp: str | None):
        """Mark a post as processed. Updates dedup state and triggers save if needed."""
        if post_id is not None:
            self.mark_seen(post_id)
        self.last_timestamp = timestamp
        self.stats["total_processed"] += 1
        self._posts_since_save += 1
        self.save()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def should_stop(self, post_timestamp: str | None) -> bool:
        """True if the post is older than the configured max_age_days."""
        if not post_timestamp:
            return False
        try:
            if isinstance(post_timestamp, str):
                for fmt in [
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%dT%H:%M:%S",
                ]:
                    try:
                        post_date = datetime.strptime(post_timestamp, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return False
            else:
                post_date = post_timestamp

            cutoff = datetime.utcnow() - timedelta(days=self.config["max_age_days"])
            return post_date < cutoff
        except Exception:
            return False

    def increment_events(self):
        self.stats["events_found"] += 1

    def set_running(self, is_running: bool):
        if is_running:
            self.stats["start_time"] = datetime.utcnow().isoformat() + "Z"
        else:
            self.stats["last_run"] = datetime.utcnow().isoformat() + "Z"

    def reset_batch(self):
        """Clear seen IDs and counters — use before a fresh re-fetch."""
        self._seen_ids.clear()
        self._seen_ids_set.clear()
        self.stats["total_processed"] = 0
        self.stats["events_found"] = 0
        self.save(force=True)
        print("🔄 State reset.")

    def clear_recent_ids(self):
        """Alias for tests."""
        self._seen_ids.clear()
        self._seen_ids_set.clear()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_state: StreamState | None = None


def get_state() -> StreamState:
    global _state
    if _state is None:
        _state = StreamState()
    return _state


def reset_state():
    """Reset the global singleton (useful for testing)."""
    global _state
    _state = None