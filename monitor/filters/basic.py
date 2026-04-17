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

class KeywordFilter(Stage):
    """ Drop posts with no announcement-related keywords. """
    name = "keyword"

    KEYWORDS = [
        # event language
        "event", "happening", "tonight", "tomorrow", "this weekend",
        "saturday", "sunday", "friday", "this thursday", "next week",
        # gathering language
        "meetup", "meet up", "gathering", "come join", "join us",
        "everyone welcome", "open to all", "free admission",
        # opportunity language
        "volunteer", "volunteers", "opportunity", "sign up", "register",
        "tickets", "rsvp", "apply",
        # hosting language
        "hosting", "presenting", "announcing", "invite", "inviting",
        # activity language
        "workshop", "class", "seminar", "pop-up", "market", "festival",
        "concert", "show", "exhibit", "tour", "trivia", "game night",
        "hike", "hiking", "ride", "yoga", "screening",
    ]

    def __init__(self, keywords: list[str] | None = None):
        self.keywords = [k.lower() for k in (keywords or self.KEYWORDS)]

    def matches(self, post: Post) -> bool:
        text_lower = post.text.lower()
        return any(kw in text_lower for kw in self.keywords)

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