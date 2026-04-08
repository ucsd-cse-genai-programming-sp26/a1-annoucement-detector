import json

def label_cli():
    labeled_data = []
    with open("data/raw_posts.jsonl", "r") as f:
        posts = [json.loads(line) for line in f]

    for p in posts[:50]: # Aim for 50
        text = p['record']['text']
        print(f"\n--- POST ---\n{text}")
        label = input("Is this an event? (y/n): ")
        labeled_data.append({"text": text, "label": 1 if label == 'y' else 0})

    with open("data/gold.jsonl", "w") as f:
        for item in labeled_data:
            f.write(json.dumps(item) + "\n")

if __name__ == "__main__":
    label_cli()