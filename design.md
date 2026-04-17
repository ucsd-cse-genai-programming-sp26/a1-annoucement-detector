### 1. Transition from Reddit to BlueSky
- **Decision:** I decided to pivot the data source from Reddit to BlueSky after encountering silent failures with the Reddit API dashboard (Responsible Builder Policy loop).
- **Agency:** **90% Me / 10% Agent.** I made the decision to switch to ensure the project remained on schedule for the Tuesday deadline. I used AI agent to help with initial connection structure.

### 2. Offline Batch Collection vs. Live Streaming

- **Decision:** I chose to collect data in offline batches rather than building a live streaming system. The fetch script downloads up to 500 posts at a time from the BlueSky firehose and saves them to a local JSONL file, which the pipeline then processes separately.
- **Agency:** Agency: 85% Me / 15% Agent. I made the call to go offline after recognizing I have no background in WebSocket or server infrastructure, and community event announcements on BlueSky don't appear fast enough to justify real-time monitoring. I asked the agent to confirm the tradeoffs and help structure the fetch script with a skip-if-exists guard so re-running never overwrites already-collected data. If I were to scale this up, the right approach would be scheduled batch downloads rather than a live stream, since the data doesn't change fast enough to justify the added complexity.

### 3.Profanity Filter
- **Decision:** I added a profanity filter that rejects inappropriate post.
- **Agency:** **90% Me / 10% Agent.** Working with public social media data, I recognized that filtering profanity was necessary to keep results appropriate for a community events use case. I made the decision to include this stage and asked the agent to suggest a lightweight package to implement it.
  
### 4. Asymmetric LLM Pipeline (Classify vs. Extract)
- **Decision:**  I added a second LLM call to extract structured event details (name, date, location, description) from posts that had already been confirmed as events by the first classification call.
- **Agency:** **30% Me / 70% Agent.** I initially only planned a single LLM call to classify whether a post was an event. The agent pointed out that confirmed events also needed structured details to be actually useful, and suggested adding a second extraction call that only runs on posts that passed classification. I agreed with the design and chose what fields to extract.

### 5. Transition to Firehose Streaming

- **Dual Mode Support:** Upgrading from offline batch downloads to real-time firehose streaming while maintaining backward compatibility with batch mode. Supports both streaming (`--stream` flag) and batch processing modes.
- **Hybrid Deduplication:** Uses a shared persistent state file to avoid duplicates across both batch and streaming modes. A rolling cache still keeps the last 1000 IDs in memory, while a persistent `processed_ids` set in `data/state.json` prevents re-processing or duplicate output across runs.
- **State Persistence:** Saves streaming state (and the cross-mode dedupe index) to `data/state.json` every 100 posts or 30 seconds, with force-save on graceful shutdown (Ctrl+C).
- **Time-Based Cutoff:** Automatically stops streaming when posts older than 60 days are encountered.
- **Graceful Shutdown:** Signal handlers capture SIGINT/SIGTERM to save state immediately and close connections cleanly.
- **No New Credentials:** Uses the same Bluesky credentials (handle + app password) - no new API keys required.
- **Resource Efficiency:** Memory usage remains constant (~100KB for ID cache); network usage ~1-10 MB/hour.
