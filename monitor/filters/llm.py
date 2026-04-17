import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from .base import Stage, Post

load_dotenv()

def _get_client():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not found in .env file.")
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


class LLMClassifyStage(Stage):
    """
    Stage 4: Ask DeepSeek 'is this a real event?' — cheap Yes/No call.
    Only posts that pass this reach the more expensive extraction step.
    """
    name = "llm_classify"

    def __init__(self):
        self.client = _get_client()

    def matches(self, post: Post) -> bool:
        prompt = (
            "You are an event detection bot. Is the following text a concrete "
            "event announcement with a specific activity and time/place? "
            "Ignore personal opinions or general news. Reply only 'Yes' or 'No'.\n\n"
            f"Text: {post.text}"
        )
        try:
            res = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=5
            )
            return "yes" in res.choices[0].message.content.strip().lower()
        except Exception as e:
            print(f"[LLMClassifyStage] Error: {e}")
            return False


class LLMExtractStage:
    """
    Final step: extract structured event details as JSON.
    Not a Stage subclass — returns data, not a boolean.
    Only called after all Stage filters pass.
    """
    def __init__(self):
        self.client = _get_client()

    def extract(self, post: Post) -> dict:
        prompt = (
            "You are an event detection and extraction assistant."
            "First decide whether the following text is a concrete event announcement with a specific activity and time/place."
            "If yes, extract these fields into valid JSON: "
            "- event_name"
            "- date"
            "- location"
            "- description"
            "If no, return: "
            "{\n  \"event_name\": null,\n  \"date\": null,\n  \"location\": null,\n  \"description\": null\n}"
            "Return only valid JSON and no extra text.\n\n"
            f"Text: {post.text}"
        )
        try:
            res = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(res.choices[0].message.content)
        except Exception as e:
            print(f"[LLMExtractStage] Error: {e}")
            return {"error": "Extraction failed"}