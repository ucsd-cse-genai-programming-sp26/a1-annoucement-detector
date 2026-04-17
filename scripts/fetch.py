"""
fetch.py — Bluesky firehose streaming and batch fetching.

Provides two modes:
1. FirehoseStream: Real-time streaming from Bluesky firehose
2. fetch_bluesky: Batch fetching (legacy, for backward compatibility)
"""
import json
import os
import sys
import signal
from datetime import datetime, timedelta
from dotenv import load_dotenv
from atproto import Client, FirehoseSubscribeReposClient, parse_subscribe_repos_message

load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.state import get_state, StreamState

# Legacy batch fetching function (for backward compatibility)
def fetch_bluesky(query=None, limit=500):
    """
    Legacy batch fetching function.
    Downloads up to `limit` posts and saves them to raw_posts.jsonl.
    If `query` is provided, search_posts will use that filter; otherwise
    it fetches from the broader feed without a query parameter.
    """
    handle = os.getenv("BSKY_HANDLE")
    password = os.getenv("BSKY_APP_PASSWORD")

    if not handle or not password:
        raise ValueError("BSKY_HANDLE and BSKY_APP_PASSWORD must be set in your .env file.")

    client = Client()
    client.login(handle, password)

    posts = []
    cursor = None

    # BlueSky returns max 100 per request, so loop until we hit limit
    while len(posts) < limit:
        batch_size = min(100, limit - len(posts))
        params = {"limit": batch_size}
        if query:
            params["q"] = query
        if cursor:
            params["cursor"] = cursor

        response = client.app.bsky.feed.search_posts(params)
        batch = response.posts

        if not batch:
            break

        posts.extend(batch)
        cursor = getattr(response, "cursor", None)
        if not cursor:
            break

    os.makedirs("data", exist_ok=True)
    with open("data/raw_posts.jsonl", "w", encoding="utf-8") as f:
        for p in posts:
            f.write(json.dumps(p.dict()) + "\n")

    print(f"Fetched {len(posts)} posts for query: '{query}'")


class FirehoseStream:
    """
    Real-time streaming from Bluesky firehose.
    
    Features:
    - Continuous streaming with callback-based processing
    - Graceful shutdown on SIGINT/SIGTERM
    - Automatic deduplication using state management
    - Time-based cutoff (stops at 60-day-old posts)
    - Resumable from last checkpoint
    """
    
    def __init__(self, callback=None):
        """
        Initialize firehose stream.
        
        Args:
            callback: Function to call for each post. Should accept a raw post dict.
                     Returns True to continue, False to stop.
        """
        self.callback = callback
        self.running = False
        self.client = None
        self.state = get_state()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
    
    def _shutdown_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print("\n⚡ Shutdown signal received, stopping stream...")
        self.running = False
    
    def set_callback(self, callback):
        """Set or update the callback function."""
        self.callback = callback
    
    def start(self):
        """Start the firehose stream."""
        if self.running:
            print("Stream is already running")
            return
        
        self.running = True
        self.state.set_running(True)
        
        print("🔥 Starting Bluesky firehose stream...")
        print(f"   Cutoff: {self.state.config['max_age_days']} days")
        print(f"   Deduplication cache: {self.state.config['recent_ids_limit']} posts")
        print("   Press Ctrl+C to stop gracefully")
        print()
        
        try:
            # Create firehose client
            self.client = FirehoseSubscribeReposClient()
            
            # Start the firehose client
            for message in self.client.stream():
                if not self.running:
                    break
                
                try:
                    # Parse the message
                    message_data = parse_subscribe_repos_message(message)
                    
                    # Only process commit messages
                    if not hasattr(message_data, 'commit') or not message_data.commit:
                        continue
                    
                    # Extract post data from the commit
                    commit = message_data.commit
                    if not hasattr(commit, 'record') or not commit.record:
                        continue
                    
                    # Check if it's a post creation
                    if not hasattr(commit, 'operation') or commit.operation != 'create':
                        continue
                    
                    # Build post data structure
                    post_data = self._process_commit(message_data)
                    if not post_data:
                        continue
                    
                    # Check for duplicates
                    post_id = post_data.get("uri")
                    if self.state.is_duplicate(post_id):
                        continue
                    
                    # Check timestamp cutoff
                    timestamp = post_data.get("record", {}).get("createdAt")
                    if self.state.should_stop(timestamp):
                        print(f"\n⏰ Reached {self.state.config['max_age_days']}-day cutoff, stopping stream...")
                        self.running = False
                        break
                    
                    # Process the post
                    if self.callback:
                        should_continue = self.callback(post_data)
                        if not should_continue:
                            self.running = False
                            break
                    
                    # Mark as processed
                    self.state.mark_processed(post_id, timestamp)
                    
                except Exception as e:
                    # Log error but continue streaming
                    if self.running:
                        print(f"Error processing message: {e}")
                    continue
            
        except KeyboardInterrupt:
            print("\n⚡ Stream interrupted")
        except Exception as e:
            print(f"❌ Firehose error: {e}")
        finally:
            self.stop()
    
    def _process_commit(self, message_data):
        """Extract post data from a commit message."""
        try:
            commit = message_data.commit
            record = commit.record
            
            # Build a post-like structure similar to search_posts format
            post_data = {
                "uri": f"at://{commit.repo}/app.bsky.feed.post/{commit.uri.split('/')[-1]}",
                "cid": commit.cid,
                "record": {
                    "text": record.text if hasattr(record, "text") else "",
                    "createdAt": record.createdAt.isoformat() + "Z" if hasattr(record, "createdAt") else None,
                    "langs": record.langs if hasattr(record, "langs") else [],
                },
                "author": {
                    "handle": commit.repo,
                    "did": commit.repo,  # Simplified, actual DID would need resolution
                },
                "indexedAt": datetime.utcnow().isoformat() + "Z",
                # Firehose doesn't provide these, but we can set defaults
                "likeCount": 0,
                "replyCount": 0,
                "repostCount": 0,
                "quoteCount": 0,
            }
            
            return post_data
            
        except Exception as e:
            if self.running:
                print(f"Error extracting post data: {e}")
            return None
    
    def stop(self):
        """Stop the firehose stream gracefully."""
        self.running = False
        self.state.set_running(False)
        
        # Force save state
        self.state.save(force=True)
        
        # Close firehose client
        if self.client:
            try:
                self.client.close()
            except:
                pass
        
        print(f"\n✅ Stream stopped")
        print(f"   Total processed: {self.state.stats['total_processed']}")
        print(f"   Events found: {self.state.stats['events_found']}")
    
    def is_running(self):
        """Check if the stream is currently running."""
        return self.running


def stream_firehose(callback=None):
    """
    Convenience function to start firehose streaming.
    
    Args:
        callback: Optional callback function for processing posts.
                 If not provided, posts will be saved to raw_posts.jsonl.
    """
    stream = FirehoseStream(callback)
    stream.start()


# Default callback for saving posts to file (similar to batch mode)
def _default_save_callback(post_data):
    """Default callback that saves posts to raw_posts.jsonl."""
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/raw_posts.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(post_data) + "\n")
        return True
    except Exception as e:
        print(f"Error saving post: {e}")
        return False


if __name__ == "__main__":
    # If run directly, start streaming with default save callback
    print("Starting firehose streaming (saving to data/raw_posts.jsonl)...")
    print("Press Ctrl+C to stop.\n")
    stream_firehose(_default_save_callback)