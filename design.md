### 1. Transition from Reddit to BlueSky
- **Decision:** I decided to pivot the data source from Reddit to BlueSky after encountering silent failures with the Reddit API dashboard (Responsible Builder Policy loop).
- **Agency:** **90% Me / 10% Agent.** I made the final executive decision to switch to ensure the project remained on schedule for the Tuesday deadline. The AI agent suggested BlueSky as a viable alternative that did not require a complex API approval process and provided the initial connection structure.

### 2. Implementation of a 60-Character Length Filter
- **Decision:** I added a heuristic filter that rejects any post under 60 characters as Stage 2 of the pipeline.
- **Agency:** **50% Me / 50% Agent.** During the manual labeling of the gold dataset, I noticed that a significant number of false positives were extremely short (e.g., "See you there!"). I asked the agent for a "zero-cost" way to reduce these, and it suggested a character-count filter. I chose the "60" threshold myself after testing different values and checking the impact on recall.

### 3. Asymmetric LLM Pipeline (Classify vs. Extract)
- **Decision:** I structured the LLM logic into two distinct calls: a high-speed "Yes/No" classification using a simple prompt, followed by a separate JSON extraction call only if the first stage passed.
- **Agency:** **30% Me / 70% Agent.** The agent proposed this "funnel" architecture to optimize for cost and latency. While I requested a way to get structured data, the agent designed the conditional logic that ensures the more expensive "Extraction" prompt is only run on posts already confirmed as events by the cheaper "Classification" prompt.
