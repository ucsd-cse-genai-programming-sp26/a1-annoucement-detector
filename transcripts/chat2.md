# chat 2
**User:**   
**Created:** 4/7/2026 13:36:33  
**Updated:** 4/8/2026 0:00:30  
**Exported:** 4/8/2026 22:23:45  
**Link:** [https://chatgpt.com/c/69d56ab9-4224-83e8-b21f-88dc41a72dea](https://chatgpt.com/c/69d56ab9-4224-83e8-b21f-88dc41a72dea)  

## Prompt:
2026/4/7 23:00:30

I have the idea to detect event using reddit on r/sandiegosocial, how to use the reddit api to get dta

## Response:
2026/4/7 23:00:31

Perfect—this is a **great, clean idea** and _r/sandiegosocial_ is an even better choice than general San Diego 👍  
Now let’s get you **from 0 → working data download** as simply as possible.

* * *

🧰 Step 1: Install what you need
================================

In terminal:

```
pip install praw python-dotenv
```

* * *

🔑 Step 2: Get Reddit API credentials
=====================================

Go to:  
👉 [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)

Create an app:

*   type: **script**
*   name: anything (e.g. `sd-event-monitor`)

You’ll get:

*   `client_id`
*   `client_secret`

* * *

📁 Step 3: Create `.env` file
=============================

In your project folder:

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=sd-event-monitor
```

* * *

🧠 Step 4: Python script to download posts
==========================================

Start with this **simple version (copy-paste and run)**:

```
import praw
import json
import os
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

subreddit = reddit.subreddit("sandiegosocial")

posts = []

for post in subreddit.new(limit=100):  # get ~100 recent posts
    posts.append({
        "id": post.id,
        "title": post.title,
        "selftext": post.selftext,
        "url": post.url,
        "created_utc": post.created_utc
    })

# save to JSON
with open("sd_posts.json", "w", encoding="utf-8") as f:
    json.dump(posts, f, indent=2)

print(f"Saved {len(posts)} posts!")
```

* * *

📂 What you get (example output)
================================

```
[
  {
    "id": "abc123",
    "title": "Pickleball meetup this Sunday",
    "selftext": "Join us at 10am...",
    "url": "https://...",
    "created_utc": 1710000000
  }
]
```

* * *

👀 Step 5: Inspect your data (IMPORTANT)
========================================

Add this after loading:

```
for p in posts[:10]:
    print(p["title"])
```

👉 Check:

*   Do you see events?
*   Do you see noise?

This will guide your labeling later.

* * *

⚠️ Important tips (save you trouble)
====================================

1\. Use `.new()` not `.hot()`
-----------------------------

```
subreddit.new(limit=100)
```

👉 gets **recent events**, which is what you want

* * *

2\. Don’t fetch comments (for now)
----------------------------------

Skip:

```
post.comments
```

👉 too messy, unnecessary

* * *

3\. Save once, reuse forever
----------------------------

Your `sd_posts.json` =  
👉 your **dataset + eval data**

* * *

🚀 Optional (slightly better version)
=====================================

If you want **more variety**, also pull:

```
for post in subreddit.hot(limit=50):
```

Combine both:

*   `new` → recent
*   `hot` → popular

* * *

🎯 What you have now
====================

After this step:

*   ✅ ~100 Reddit posts
*   ✅ Ready for labeling
*   ✅ Ready for pipeline

* * *

👉 Next step (don’t skip this)
==============================

The **most important next step**:

👉 labeling rules
-----------------

Example:

*   “Yoga meetup Saturday” → YES
*   “Any yoga meetups?” → NO

* * *

If you want, I’ll give you:

*   a **clean labeling guide (so your eval is solid)**
*   and your **LLM prompt for event detection**

Just say “next step” 👍

## Prompt:
2026/4/7 23:01:24

![Uploaded image](https://chatgpt.com/backend-api/estuary/content?id=file_00000000998071fb8325921a5b395feb&ts=493253&p=fs&cid=1&sig=e7f68575493a0aff953a5548850eb0122598e16ed6324258954a71328eefb1e6&v=0)

do you need an url for it?

## Response:
2026/4/7 23:01:25

Good question—this part is confusing but actually simple 👍

✅ For your case (script app):
-----------------------------

👉 **YES, you need to fill “redirect uri”**  
👉 **BUT it can be anything (dummy URL)**

* * *

🎯 What to put
==============

Just enter:

```
http://localhost:8080
```

or

```
http://127.0.0.1:8080
```

* * *

🤔 Why is this required?
========================

*   Reddit requires a redirect URI for OAuth apps
*   BUT for **“script” type apps**, you **won’t actually use it**

👉 So it’s just a formality

* * *

✅ Your final setup should look like:
====================================

*   ✔ type: **script** (correct)
*   ✔ name: anything
*   ✔ description: optional
*   ✔ redirect uri: `http://localhost:8080`

Then click **create app**

* * *

🔑 After you create it
======================

You’ll see:

*   client ID (short string under app name)
*   client secret

👉 These go into your `.env`

* * *

🚀 You’re almost there
======================

After this step:

*   API setup = done
*   next = run your Python script and download posts

* * *

If you want next, I can:  
👉 check your `.env` + code  
👉 or help you write the **event detection prompt + labeling rules**

Just say 👍



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)