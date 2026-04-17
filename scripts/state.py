"""
state.py — State management for firehose streaming.

Handles persistence of streaming state to enable resumable processing:
- Last checkpoint timestamp
- Recent post IDs for deduplication
- Processing statistics
"""
import json
import os
from datetime import datetime, timedelta
from collections import deque

STATE_PATH = "data/state.json"

class StreamState:
    """Manages streaming state for resumable firehose processing."""
    
    def __init__(self, state_path=STATE_PATH):
        self.state_path = state_path
        self.recent_ids = deque(maxlen=1000)  # Keep last 1000 post IDs
        self.processed_ids = set()              # Persistent dedupe across batch and stream
        self.last_timestamp = None
        self.stats = {
            "total_processed": 0,
            "events_found": 0,
            "last_run": None,
            "start_time": None,
        }
        self.config = {
            "max_age_days": 60,
            "recent_ids_limit": 1000,
            "save_interval_posts": 100,
            "save_interval_seconds": 30,
        }
        self._posts_since_save = 0
        self._last_save_time = datetime.utcnow()
        
        # Load existing state if available
        self.load()
    
    def load(self):
        """Load state from file if it exists."""
        if not os.path.exists(self.state_path):
            return
        
        try:
            with open(self.state_path, "r") as f:
                data = json.load(f)
            
            self.last_timestamp = data.get("last_timestamp")
            
            # Load recent IDs into deque
            recent_ids = data.get("recent_ids", [])
            self.recent_ids = deque(recent_ids, maxlen=self.config["recent_ids_limit"])
            self.processed_ids = set(data.get("processed_ids", []))
            
            # Load stats
            saved_stats = data.get("stats", {})
            self.stats.update(saved_stats)
            
            # Load config overrides
            saved_config = data.get("config", {})
            self.config.update(saved_config)
            
            print(f"Loaded state from {self.state_path}")
            print(f"  Last timestamp: {self.last_timestamp}")
            print(f"  Recent IDs: {len(self.recent_ids)}")
            print(f"  Processed IDs: {len(self.processed_ids)}")
            print(f"  Total processed: {self.stats['total_processed']}")
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load state file: {e}")
            print("Starting with fresh state.")
    
    def save(self, force=False):
        """Save state to file. Force save ignores interval checks."""
        should_save = force
        
        # Check if we've hit the post interval
        if not should_save:
            should_save = self._posts_since_save >= self.config["save_interval_posts"]
        
        # Check if we've hit the time interval
        if not should_save:
            time_since_save = datetime.utcnow() - self._last_save_time
            should_save = time_since_save.total_seconds() >= self.config["save_interval_seconds"]
        
        if not should_save:
            return False
        
        # Perform save
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            
            data = {
                "last_timestamp": self.last_timestamp,
                "recent_ids": list(self.recent_ids),
                "processed_ids": list(self.processed_ids),
                "stats": self.stats,
                "config": self.config,
            }
            
            # Write to temporary file first, then rename (atomic operation)
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
                print(f"State saved (force) to {self.state_path}")
            
            return True
            
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
    
    def mark_processed(self, post_id, timestamp):
        """Mark a post as processed. Updates state and checks if save is needed."""
        if post_id is not None:
            self.processed_ids.add(post_id)
            self.recent_ids.append(post_id)
        self.last_timestamp = timestamp
        self.stats["total_processed"] += 1
        self._posts_since_save += 1
        
        # Try to save (will only save if interval reached)
        self.save()
    
    def is_duplicate(self, post_id):
        """Check if a post has already been processed."""
        return post_id in self.processed_ids
    
    def should_stop(self, post_timestamp):
        """Check if we've reached the time-based cutoff."""
        if not post_timestamp:
            return False
        
        try:
            # Parse timestamp (handle both string and datetime)
            if isinstance(post_timestamp, str):
                # Try common formats
                for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        post_date = datetime.strptime(post_timestamp, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return False  # Can't parse, don't stop
            else:
                post_date = post_timestamp
            
            cutoff_date = datetime.utcnow() - timedelta(days=self.config["max_age_days"])
            return post_date < cutoff_date
            
        except Exception:
            return False
    
    def increment_events(self):
        """Increment the events found counter."""
        self.stats["events_found"] += 1
    
    def set_running(self, is_running):
        """Update running state."""
        if is_running:
            self.stats["start_time"] = datetime.utcnow().isoformat() + "Z"
        else:
            self.stats["last_run"] = datetime.utcnow().isoformat() + "Z"
    
    def clear_recent_ids(self):
        """Clear the recent IDs cache (useful for testing)."""
        self.recent_ids.clear()


# Global state instance (lazy initialization)
_state = None

def get_state():
    """Get the global state instance."""
    global _state
    if _state is None:
        _state = StreamState()
    return _state

def reset_state():
    """Reset the global state (useful for testing)."""
    global _state
    _state = None