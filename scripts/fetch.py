import json
import os
from dotenv import load_dotenv
from atproto import Client

load_dotenv()

def fetch_bluesky(query="San Diego event", limit=500):
    handle = os.getenv("BSKY_HANDLE")
    password = os.getenv("BSKY_APP_PASSWORD")

    if not handle or not password:
        raise ValueError("BSKY_HANDLE and BSKY_APP_PASSWORD must be set in your .env file.")

    client = Client()
    client.login(handle, password)

    posts = []
    cursor = None

    # BlueSky returns max 100 per request, so loop until we hit limit
    while len(posts) < limit:
        batch_size = min(100, limit - len(posts))
        params = {"q": query, "limit": batch_size}
        if cursor:
            params["cursor"] = cursor

        response = client.app.bsky.feed.search_posts(params)
        batch = response.posts

        if not batch:
            break

        posts.extend(batch)
        cursor = getattr(response, "cursor", None)
        if not cursor:
            break

    os.makedirs("data", exist_ok=True)
    with open("data/raw_posts.jsonl", "w", encoding="utf-8") as f:
        for p in posts:
            f.write(json.dumps(p.dict()) + "\n")

    print(f"Fetched {len(posts)} posts for query: '{query}'")

if __name__ == "__main__":
    fetch_bluesky()