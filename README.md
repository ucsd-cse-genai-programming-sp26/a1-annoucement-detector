# A1 — Announcement Detector

## Project Description

This project built an LLM-powered social media monitor that detects local community event announcements from BlueSky posts, targeting San Diego meetups, workshops, parties, and gatherings. 
A multi-stage pipeline is designed to progressively filter out reposts, noise, and casual conversation before using Deepseek-V3.2 to confirm and extract structured event details.

---

## Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd a1-announcement-detector
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API keys

Copy the example env file and fill in your credentials:
```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```
BSKY_HANDLE=yourhandle.bsky.social
BSKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
DEEPSEEK_API_KEY=your-deepseek-key-here
```

- **BSKY_HANDLE / BSKY_APP_PASSWORD**: Your BlueSky username and an App Password. Generate one at BlueSky → Settings → Privacy and Security → App Passwords.
- **DEEPSEEK_API_KEY**: DeepSeek API key.

---

## How to Run

### 1. Collect & Label Data
```bash
# Fetch 500 posts from BlueSky (batch mode)
python -m scripts.fetch

# Manually label 50 posts to build the gold dataset
python -m scripts.label
```

### 2. Run the Pipeline

The pipeline supports two modes: **batch** (from saved posts) and **streaming** (live from firehose).

#### Batch Mode (default)
```bash
# Run pipeline on all fetched posts, print and save detected events
python -m scripts.run_pipeline
```

#### Streaming Mode (real-time)
```bash
# Stream posts live from Bluesky firehose and process in real-time
python -m scripts.run_pipeline --stream

# Stop streaming gracefully with Ctrl+C (state is saved automatically)
```

**Streaming Features:**
- Real-time processing of posts as they appear on Bluesky
- Automatic deduplication - restart without processing duplicates
- State persistence in `data/state.json` for resumable streaming
- Auto-stops at 60-day-old posts to avoid processing historical data
- Graceful shutdown with Ctrl+C saves all progress

### 3. Evaluate
```bash
# Basic run, no label
python -m scripts.evaluate

# Label the run for easier comparison later
python -m scripts.evaluate "baseline"
python -m scripts.evaluate "new classify prompt"
```

Each run appends to two CSV files in `data/`.

---

## Demo Video
**[Demo Video — YouTube Link](https://youtu.be/tTKSz8C1DHI)**

---

## Eval Results

Measured on 50 manually labeled BlueSky posts.

| Metric         | Value |
|----------------|-------|
| Precision      | 0.50 |
| Recall         | 0.20 |
| F1             | 0.29 |

Prediction Details: TP: 2, FP: 2, FN: 8, TN: 35

#### Discussion:
The new pipeline shows lower recall and precision compared to the initial version due to significant changes in data collection strategy:

- **Broader fetch query impact**: Switching from a narrow search phrase ("san diego event") to broader terms ("ca", "california", "san diego", "sd") changes the data composition. The 498 downloaded posts now contain far fewer actual event announcements, so the low TP count (2) reflects a data problem — real events are simply rarer in a general-chatter pool.

- **Keyword filter limitations**: The keyword filter may discard legitimate announcements lacking standard event vocabulary, contributing to false negatives.

- **Incomplete event details**: Many BlueSky event announcements offload key details (date, location, venue) to attached images or external links. Since the pipeline only processes post text, the LLM extracts nothing meaningful for these posts and rejects them. 

### Per-Stage Breakdown

| Stage        | In  | Out | Dropped | Notes                           |
|--------------|-----|-----|---------|--------------------------------|
| metadata     | 498 | 486 | 12      | Drops reposts, non-English      |
| length       | 486 | 448 | 38      | Keeps 60–500 chars              |
| keyword      | 448 | 178 | 270     | Removes non-event vocabulary    |
| profanity    | 178 | 170 | 8       | Drops profane posts             |
| llm_extract  | 170 | 170 | 0       | Single LLM call: classify + extract |
| **TOTAL**    | **498** | **170** | **328**  | **Pass rate: 34.1%**            |

### Stats files
Every `evaluate` run appends to two CSV files, allowing systematic comparison across prompt changes and pipeline configurations.

**`data/eval_runs.csv`** — one row per run, summarized metrics:
```
run_id | timestamp | label | precision | recall | f1 | cost_usd | stage_*_out ...
```

**`data/eval_samples.csv`** — one row per post per run, individual predictions:
```
run_id | timestamp | label | post_id | text | true_label | predicted | correct
```

**`data/pipeline_runs.csv`** — one row per `run_pipeline` run, with per-stage post counts and estimated cost. Useful for tracking how the pipeline behaves on real data over time.

---

## Pipeline Stages

**1. MetadataFilter**: Drops reposts and non-English posts using BlueSky's built-in metadata fields (`reason`, `langs`).

**2. LengthFilter**: Keeps posts between 60 and 500 characters. Below 60 is casual noise; above 500 is typically a news article or rant.

**3. KeywordFilter**: Removes posts lacking event-related vocabulary (dates, times, locations, event keywords). Significantly reduces noise before the expensive LLM stage.

**4. ProfanityFilter**: Drops posts containing profanity using the `better-profanity` library.

**5. LLMExtractStage**: Single unified DeepSeek call that both confirms the post is an event announcement and extracts structured details: `event_name`, `date`, `location`, `description` as JSON. Replaces the previous two-stage LLM pipeline.

---

## Project Structure

```
a1-announcement-detector/
├── .env                         # credentials
├── requirements.txt
├── README.md
├── DESIGN.md
├── data/
│   ├── raw_posts.jsonl          # fetched BlueSky posts (batch mode)
│   ├── state.json               # streaming state (resumable progress)
│   ├── gold.jsonl               # 50 manually labeled posts
│   ├── detected_events.jsonl    # events found by run_pipeline
│   ├── eval_runs.csv            # evaluate run (summary)
│   ├── eval_samples.csv     
│   └── pipeline_runs.csv
├── transcripts/                
├── monitor/
│   ├── __init__.py
│   ├── pipeline.py              # assembles stages into EventPipeline
│   └── filters/
│       ├── __init__.py
│       ├── base.py              # Stage base class + Post dataclass
│       ├── basic.py             # MetadataFilter, LengthFilter, ProfanityFilter
│       └── llm.py               # LLMClassifyStage, LLMExtractStage
└── scripts/
    ├── fetch.py                 # fetch posts (batch) or stream (firehose)
    ├── state.py                 # state management for streaming
    ├── label.py                 # manual labeling CLI
    ├── run_pipeline.py          # run pipeline (batch or streaming mode)
    └── evaluate.py              # measure precision/recall/cost
```

---

## Original V1 Pipeline (for reference)

**Fetch Query**: Narrow phrase: "san diego event"  
**LLM Approach**: Two separate calls (classify, then extract)

| Stage        | In  | Out | Dropped |
|--------------|-----|-----|---------|
| metadata     | 500 | 496 | 4       |
| length       | 496 | 487 | 9       |
| profanity    | 487 | 487 | 0       |
| llm_classify | 487 | 302 | 185     |
| llm_extract  | 302 | 302 | 0       |
| **TOTAL**    | **500** | **302** | **198** |

**V1 Eval Results**: Precision: 0.7143 | Recall: 0.9375 | F1: 0.8108

---

## Differences from V1

The current V2 pipeline differs in two key ways:
1. **Broader fetch query** ("ca", "california", "san diego", "sd") instead of just "san diego event" 
2. **Added keyword filter** 
3. **Single LLM Call**

---

## AI Transcripts

Chat logs from AI-assisted development are in [`transcripts/`](./transcripts/).
