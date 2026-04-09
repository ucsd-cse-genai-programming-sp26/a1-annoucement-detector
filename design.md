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
