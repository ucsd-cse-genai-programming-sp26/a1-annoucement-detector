## Feedback
Feedback received:
- add more filters to drop more posts before the LLM step
- use one LLM call instead of two
- extract "date" into the JSON output
- include more files in `.gitignore`
- explain why the system has high recall but lower precision

## Updates

### 1. Broader fetch query
Changed the fetch criteria from a narrow phrase like `san diego event` to broader local terms: `ca`, `california`, `san diego`, and `sd`.

### 2. Keyword filter
Added a keyword filter stage after fetch to remove clearly irrelevant posts before the single LLM call.

### 3. Single LLM call + date extraction
Combined classification and extraction into one LLM invocation, extracting event name, date, location, and description.
Added `date` to the extraction schema.

### 4. Git ignore updates
Added `__pycache__/` to `.gitignore`.

### 5. High recall, lower precision
The previous announcement detector shows high recall and relatively lower precision because the evaluation data uses strict event-labeling criteria.
A post is marked as an event announcement only if it includes concrete details such as date and location.
Casual posts that mention possible plans or loosely described events can be mistaken for announcements, which increases false positives.

## New Results
```text
--- Pipeline Stats ---
Stage                    In    Out  Dropped
--------------------------------------------
metadata                498    486       12
length                  486    448       38
keyword                 448    178      270
profanity               178    170        8
llm_extract             170    170        0
--------------------------------------------
TOTAL                   498    170      328

Pass rate     : 34.1%

--- Eval Results ---
TP: 2  FP: 2  FN: 8  TN: 35
Precision : 0.50
Recall    : 0.20
F1        : 0.29

### Discussion: 
The new result has a much lower recall and precision, which could be due to: 
- Switching to a broader fetch query (from "san diego event" to generic terms like "california", "sd") significantly changed the data composition. The 498 downloaded posts now contain far fewer actual event announcements, so the low TP count (2) is partly a data problem — real events are simply rarer in a general-chatter pool than in a targeted one.
- The high FN count (8) has two likely causes. First, the keyword filter may discard legitimate announcements that lack standard event vocabulary. Second, many real event posts on Bluesky offload key details, like date, location, venue, to an attached image or an external link. The pipeline only sees the post text, so the LLM extracts nothing meaningful and rejects the post.

```
