from .base import Stage, Post

class MetadataFilter(Stage):
    """ 1: Drop reposts and non-English posts"""
    name = "metadata"

    def matches(self, post: Post) -> bool:
        if post.raw_data.get("reason"):         
            return False
        langs = post.raw_data.get("record", {}).get("langs", [])
        if langs and "en" not in langs:         
            return False
        return True


class LengthFilter(Stage):
    """Stage 2: filter by length"""
    name = "length"

    def __init__(self, min_length: int = 60, max_length: int = 500):
        self.min_length = min_length
        self.max_length = max_length

    def matches(self, post: Post) -> bool:
        return self.min_length <= len(post.text) <= self.max_length


class ProfanityFilter(Stage):
    """Stage 3: Drop posts containing profanity."""
    name = "profanity"

    def __init__(self):
        try:
            from better_profanity import profanity
            profanity.load_censor_words()
            self._checker = profanity
            self.enabled = True
        except ImportError:
            print("Warning: better-profanity not installed, skipping this stage.")
            print("Fix with: pip install better-profanity")
            self.enabled = False

    def matches(self, post: Post) -> bool:
        if not self.enabled:
            return True
        return not self._checker.contains_profanity(post.text)