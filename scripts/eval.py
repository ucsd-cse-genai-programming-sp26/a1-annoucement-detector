import json
from monitor.pipeline import EventPipeline
from monitor.filters.base import Post

def run_eval():
    pipeline = EventPipeline()
    with open("data/gold.jsonl", "r") as f:
        gold_set = [json.loads(line) for line in f]

    tp, fp, fn, tn = 0, 0, 0, 0
    
    for item in gold_set:
        # Mock a Post object for the pipeline
        mock_post = Post(id="1", text=item['text'], author="user", created_at="now", raw_data={})
        result = pipeline.run(mock_post)
        
        pred = 1 if result else 0
        actual = item['label']

        if pred == 1 and actual == 1: tp += 1
        elif pred == 1 and actual == 0: fp += 1
        elif pred == 0 and actual == 1: fn += 1
        else: tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    print(f"Results: Precision {precision:.2f}, Recall {recall:.2f}")

if __name__ == "__main__":
    run_eval()