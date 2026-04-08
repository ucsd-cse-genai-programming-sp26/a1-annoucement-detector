from .base import BaseFilter, Post

class LengthFilter(BaseFilter):
    def __init__(self, min_length: int = 60):
        self.min_length = min_length

    def process(self, post: Post) -> bool:
        # Filter out short, casual "noise"
        return len(post.text) >= self.min_length

class KeywordFilter(BaseFilter):
    def __init__(self, keywords: list):
        self.keywords = [k.lower() for k in keywords]

    def process(self, post: Post) -> bool:
        text = post.text.lower()
        return any(kw in text for kw in self.keywords)