"""
label.py — Interactive CLI for labeling raw posts into a gold dataset.

Usage:
    python -m scripts.label           # label up to 50 posts
    python -m scripts.label --limit 100
"""
import json
import os
import sys
import argparse

RAW_POSTS_PATH = "data/raw_posts.jsonl"
GOLD_PATH      = "data/gold.jsonl"


def label_cli(limit: int = 50):
    if not os.path.exists(RAW_POSTS_PATH):
        print(f"❌ No posts file found at '{RAW_POSTS_PATH}'.")
        print("   Run 'python -m scripts.fetch' first.")
        return

    with open(RAW_POSTS_PATH, "r", encoding="utf-8") as f:
        posts = [json.loads(line) for line in f if line.strip()]

    if not posts:
        print("❌ No posts to label — raw_posts.jsonl is empty.")
        return

    # Load already-labeled IDs so we don't relabel
    labeled_ids: set = set()
    labeled_data: list = []
    if os.path.exists(GOLD_PATH):
        with open(GOLD_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    labeled_data.append(item)
                    if "id" in item:
                        labeled_ids.add(item["id"])

    to_label = [
        p for p in posts
        if p.get("uri", "") not in labeled_ids
    ][:limit]

    if not to_label:
        print(f"✅ All posts already labeled ({len(labeled_data)} in gold set).")
        return

    print(f"📝 Labeling {len(to_label)} posts (of {len(posts)} total)")
    print("   Commands: y = event, n = not event, s = skip, q = quit\n")

    newly_labeled = 0

    for i, p in enumerate(to_label, start=1):
        text = p.get("record", {}).get("text", "")
        uri  = p.get("uri", "")

        print(f"--- [{i}/{len(to_label)}] ---")
        print(text)
        print()

        while True:
            choice = input("Is this a San Diego event? (y/n/s/q): ").strip().lower()
            if choice in ("y", "n", "s", "q"):
                break
            print("  Please enter y, n, s, or q.")

        if choice == "q":
            print("\n⏹ Labeling stopped early.")
            break
        if choice == "s":
            continue

        labeled_data.append({
            "id":    uri,
            "text":  text,
            "label": 1 if choice == "y" else 0,
        })
        newly_labeled += 1
        print()

    # Overwrite gold file with full updated set
    os.makedirs("data", exist_ok=True)
    with open(GOLD_PATH, "w", encoding="utf-8") as f:
        for item in labeled_data:
            f.write(json.dumps(item) + "\n")

    pos = sum(1 for x in labeled_data if x["label"] == 1)
    neg = sum(1 for x in labeled_data if x["label"] == 0)

    print(f"\n✅ Gold dataset saved to '{GOLD_PATH}'")
    print(f"   Total labeled : {len(labeled_data)}  (+{newly_labeled} new)")
    print(f"   Events (1)    : {pos}")
    print(f"   Non-events (0): {neg}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Label raw posts for evaluation")
    parser.add_argument("--limit", type=int, default=50,
                        help="Max new posts to label this session (default: 50)")
    args = parser.parse_args()
    label_cli(limit=args.limit)