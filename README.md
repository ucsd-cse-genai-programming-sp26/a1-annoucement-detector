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
- **DEEPSEEK_API_KEY**: Your DeepSeek API key from [platform.deepseek.com](https://platform.deepseek.com).

---

## How to Run

### 1. Collect & Label Data
```bash
# Fetch 500 posts from BlueSky 
python -m scripts.fetch

# Manually label 50 posts to build the gold dataset
python -m scripts.label
```

### 2. Run the Pipeline
```bash
# Run pipeline on all fetched posts, print and save detected events
python -m scripts.run_pipeline
```

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
**[Demo Video — YouTube Link](YOUR_YOUTUBE_LINK_HERE)**

---

## Eval Results

Measured on 50 manually labeled BlueSky posts.

| Metric         | Value |
|----------------|-------|
| Precision      | 0.7143 |
| Recall         | 0.9375 |
| F1             | 0.8108 |
| Est. Cost (50 posts) | $ 0.00414 |

### Per-Stage Breakdown

| Stage        | In  | Out | Dropped | Notes                      |
|--------------|-----|-----|---------|----------------------------|
| Raw fetch    | 500 | 500 | 0       | No filtering               |
| metadata     | 500 | 496 | 4       | Drops reposts, non-English |
| length       | 496 | 487 | 9       | Keeps 60–500 chars         |
| profanity    | 487 | 487 | 0       | Drops profane posts        |
| llm_classify | 487 | 302 | 185     | DeepSeek Yes/No            |
| llm_extract  | 302 | 302 | 0       | JSON extraction            |

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

**3. ProfanityFilter**: Drops posts containing profanity using the `better-profanity` library. 

**4. LLMClassify**: Sends the post to DeepSeek with a Yes/No prompt. Only confirmed events proceed further.

**5. LLMExtractStage**: For confirmed events, a second DeepSeek call extracts `event_name`, `date`, `location`, `description` as structured JSON.

---

## Project Structure

```
a1-announcement-detector/
├── .env                         # credentials
├── requirements.txt
├── README.md
├── DESIGN.md
├── data/
│   ├── raw_posts.jsonl          # 500 fetched BlueSky posts
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
    ├── fetch.py                 # fetch posts from BlueSky
    ├── label.py                 # manual labeling CLI
    ├── run_pipeline.py          # run pipeline on raw posts
    └── evaluate.py              # measure precision/recall/cost
```

---

## AI Transcripts

Chat logs from AI-assisted development are in [`transcripts/`](./transcripts/).
