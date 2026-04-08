import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from .base import BaseFilter, Post

load_dotenv()

class DeepSeekFilter(BaseFilter):
    def __init__(self, mode="classify"):
        """
        Initializes the DeepSeek client using the API key from .env.
        mode: "classify" for filtering, "extract" for structured data gathering.
        """
        api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found. Ensure it is set in your .env file.")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.mode = mode

    def process(self, post: Post) -> bool:
        """
        Stage 3/4: High-precision classification.
        Returns True if the LLM confirms this is a concrete event.
        """
        if self.mode == "classify":
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
                decision = res.choices[0].message.content.strip().lower()
                return "yes" in decision
            except Exception as e:
                print(f"Error in DeepSeek classification: {e}")
                return False
        
        return True

    def extract(self, post: Post) -> dict:
        """
        Final Stage: Extraction.
        Only called if process() returns True.
        """
        prompt = (
            "Extract the following details from the text into a JSON object: "
            "event_name, date, location, description. "
            "If a field is missing, use 'Unknown'.\n\n"
            f"Text: {post.text}"
        )
        
        try:
            res = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={'type': 'json_object'}
            )
            # Parse the string content into a dictionary
            return json.loads(res.choices[0].message.content)
        except Exception as e:
            print(f"Error in DeepSeek extraction: {e}")
            return {"error": "Extraction failed"}