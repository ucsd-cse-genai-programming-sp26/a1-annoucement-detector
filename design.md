### 1. Transition from Reddit to BlueSky
- **Decision:** I decided to pivot the data source from Reddit to BlueSky after encountering silent failures with the Reddit API dashboard (Responsible Builder Policy loop).
- **Agency:** **90% Me / 10% Agent.** I made the decision to switch to ensure the project remained on schedule for the Tuesday deadline. I used AI agent to help with initial connection structure.

### 2. Offline Batch Collection vs. Live Streaming

- **Decision:** I chose to collect data in offline batches rather than building a live streaming system. The fetch script downloads up to 500 posts at a time from the BlueSky firehose and saves them to a local JSONL file, which the pipeline then processes separately.
- **Agency:** Agency: 85% Me / 15% Agent. I made the call to go offline after recognizing I have no background in WebSocket or server infrastructure, and community event announcements on BlueSky don't appear fast enough to justify real-time monitoring. I asked the agent to confirm the tradeoffs and help structure the fetch script with a skip-if-exists guard so re-running never overwrites already-collected data. If I were to scale this up, the right approach would be scheduled batch downloads rather than a live stream, since the data doesn't change fast enough to justify the added complexity.

### 3. Profanity Filter
- **Decision:** I added a profanity filter that rejects inappropriate post.
- **Agency:** **90% Me / 10% Agent.** Working with public social media data, I recognized that filtering profanity was necessary to keep results appropriate for a community events use case. I made the decision to include this stage and asked the agent to suggest a lightweight package to implement it.
  
### 4. Looser Query and Keyword Filter
- **Decision:** I changed the fetch query from a narrow phrase like "san diego event" to a broader set of local terms: "ca", "california", "san diego", and "sd".
- **Decision:** I also added a keyword filter stage after fetch to remove clearly irrelevant posts before reaching the LLM stage.
- **Agency:** **90% Me / 10% Agent.** I chose to capture more candidate posts with a looser query and then use keyword filtering to prune noise, rather than relying on a too-strict search phrase that misses many local announcements.

### 5. Single LLM Pipeline (Classify and Extract)
- **Decision:** I collapsed the previous two-LLM design into one unified LLM call that both confirms an event and extracts structured details in a single pass.
- **Decision:** The extracted fields now explicitly include the event name, date, location, and description.
- **Agency:** **30% Me / 70% Agent.** I initially planned separate classification and extraction calls, but moved to a single-stage LLM workflow after recognizing it would simplify the pipeline and reduce API usage while still producing the needed structured output.

## Updates

### 1. "looser query":
Changed the fetch criteria from a narrow phrase like "san diego event" to broader local terms: "ca", "california", "san diego", and "sd".

### 2. "keyword filter":
Added a keyword filter stage after fetch to remove clearly irrelevant posts before the single LLM call.

### 3. "single llm call":
Combined classification and extraction into one LLM invocation, extracting event name, date, location, and description.

## New Results
--- Pipeline Stats ---
Stage                    In    Out  Dropped
--------------------------------------------
metadata                498    486       12
length                  486    448       38
keyword                 448    178      270
profanity               178    170        8
llm_extract             170    170        0
--------------------------------------------
TOTAL                   498    170      328

Pass rate     : 34.1%