"""
evaluate.py — run the pipeline against the gold dataset and log results.

Usage:
    python -m scripts.evaluate                        # no label
    python -m scripts.evaluate "added profanity filter"
"""
import sys
import os
import json
import csv
import uuid
from datetime import datetime

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.pipeline import EventPipeline
from monitor.filters.base import Post

GOLD_PATH      = "data/gold.jsonl"
RUNS_LOG       = "data/eval_runs.csv"      # one row per run (summary)
SAMPLES_LOG    = "data/eval_samples.csv"   # one row per post per run

def run_eval(label: str = ""):
    if not os.path.exists(GOLD_PATH):
        print(f"ERROR: Gold dataset not found at '{GOLD_PATH}'.")
        print("Run 'python -m scripts.fetch' then 'python -m scripts.label' first.")
        return

    pipeline = EventPipeline()

    with open(GOLD_PATH, "r") as f:
        gold_set = [json.loads(line) for line in f]

    print(f"Evaluating on {len(gold_set)} labeled examples...\n")

    # Unique ID for this run — links runs log to samples log
    run_id    = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tp, fp, fn, tn = 0, 0, 0, 0
    sample_rows = []

    for item in gold_set:
        post = Post(
            id=item.get("id", "eval"),
            text=item["text"],
            author="user",
            created_at="now",
            raw_data={}
        )
        result  = pipeline.run(post)
        pred    = 1 if result else 0
        actual  = item["label"]
        correct = int(pred == actual)

        if pred == 1 and actual == 1: tp += 1
        elif pred == 1 and actual == 0: fp += 1
        elif pred == 0 and actual == 1: fn += 1
        else: tn += 1

        sample_rows.append({
            "run_id":    run_id,
            "timestamp": timestamp,
            "label":     label,
            "post_id":   item.get("id", ""),
            "text":      item["text"][:120],   # truncate for readability
            "true_label": actual,
            "predicted":  pred,
            "correct":    correct,
        })

    # --- Compute metrics ---
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # --- Print to terminal ---
    print("--- Eval Results ---")
    print(f"TP: {tp}  FP: {fp}  FN: {fn}  TN: {tn}")
    print(f"Precision : {precision:.2f}")
    print(f"Recall    : {recall:.2f}")
    print(f"F1        : {f1:.2f}")
    pipeline.print_stats()

    # --- Save eval_runs.csv (one row = one run) ---
    os.makedirs("data", exist_ok=True)
    run_row = {
        "run_id":    run_id,
        "timestamp": timestamp,
        "label":     label,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(precision, 4),
        "recall":    round(recall, 4),
        "f1":        round(f1, 4),
        **pipeline.get_stats_dict(),
    }
    _append_csv(RUNS_LOG, run_row)

    # --- Save eval_samples.csv (one row = one post) ---
    _append_csv(SAMPLES_LOG, sample_rows[0], sample_rows)

    print(f"\nRun ID: {run_id}")
    print(f"Summary saved to '{RUNS_LOG}'")
    print(f"Samples  saved to '{SAMPLES_LOG}'")


def _append_csv(path, first_row, all_rows=None):
    """Append rows to a CSV, writing header only if file is new."""
    if all_rows is None:
        all_rows = [first_row]
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=first_row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(all_rows)


if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else ""
    run_eval(label=label)