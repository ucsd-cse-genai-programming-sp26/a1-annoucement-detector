import requests
import json
import os

def fetch_bluesky(query="San Diego", limit=50):
    url = f"https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q={query}&limit={limit}"
    response = requests.get(url).json()
    
    os.makedirs("data", exist_ok=True)
    with open("data/raw_posts.jsonl", "w") as f:
        for p in response.get('posts', []):
            f.write(json.dumps(p) + "\n")
    print(f"Fetched {len(response.get('posts', []))} posts.")

if __name__ == "__main__":
    fetch_bluesky()