# a1-annoucement-detector

## Project Description
This project is a social media monitor designed to identify community events and gatherings from the BlueSky firehose. Using a multi-stage pipeline, it filters out casual conversation and general news to surface concrete announcements with specific times and locations, specifically targeting local community vibes and niche meetups.

## Setup
1. **Clone the repository** to your local machine.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or .\venv\Scripts\activate on Windows
   Install dependencies:
3. How to Run
 ```bash
python scripts/fetch.py
python scripts/label.py
python scripts/eval.py
4. Run Pipeline (Live/Batch)
 ```bash
python scripts/run_pipeline.py
