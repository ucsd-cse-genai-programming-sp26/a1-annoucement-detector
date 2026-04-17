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
    name = "keyword"

    # Bucket 1: San Diego location signals
    # Post must match AT LEAST ONE of these to be considered local
    LOCATION_KEYWORDS = [
        # city / region names
        "california", "ca", "cali", "san diego", "sd", "socal", "so cal", "southern california",
        # neighborhoods
        "la jolla", "mission bay", "mission beach", "ocean beach", "ob ",
        "pacific beach", "pb ", "north park", "south park", "hillcrest",
        "normal heights", "university heights", "mission hills",
        "little italy", "gaslamp", "east village", "golden hill",
        "city heights", "kensington", "talmadge", "college area",
        "el cajon", "santee", "lakeside", "spring valley",
        "chula vista", "national city", "imperial beach",
        "coronado", "point loma", "ocean hills", "mira mesa",
        "sorrento valley", "UTC", "clairemont", "linda vista",
        "mission valley", "fashion valley", "morena",
        "encinitas", "solana beach", "del mar", "cardiff",
        "oceanside", "carlsbad", "vista", "san marcos", "escondido",
        "poway", "santee", "el cajon", "lemon grove",
        # landmarks / venues people actually use
        "balboa park", "petco park", "pechanga arena", "snapdragon",
        "liberty station", "seaport village", "old town",
        "mission trails", "torrey pines", "lake murray",
        "ucsd", "sdsu", "usd", "mesa college", "city college",
        # zip codes — catches posts that skip the city name
        "921",   # all SD zip codes start with 921xx
    ]

    # Bucket 2: Announcement signal words
    # Post must match AT LEAST ONE of these to be worth sending to LLM
    ANNOUNCEMENT_KEYWORDS = [
        # time signals — strong indicator something is happening
        "tonight", "tomorrow", "this weekend", "next weekend",
        "this saturday", "this sunday", "this friday", "this thursday",
        "next saturday", "next sunday", "next friday",
        "saturday", "sunday",
        "this week", "next week", "upcoming",
        "am ", "pm ", "a.m.", "p.m.",   # time of day signals
        # action words
        "join", "come", "attend", "rsvp", "register", "sign up",
        "signup", "tickets", "free admission", "free entry",
        "volunteer", "volunteers", "apply", "applications",
        "hosting", "presenting", "announcing", "invite", "inviting",
        # event type words
        "event", "meetup", "meet up", "gathering", "workshop",
        "class", "seminar", "pop-up", "popup", "market", "festival",
        "concert", "show", "exhibit", "exhibition", "screening",
        "tour", "trivia", "game night", "open mic", "open house",
        "hike", "hiking", "ride", "yoga", "run ", "walk ",
        "sale", "swap", "fair", "cleanup", "rally", "protest",
        "happy hour", "brunch", "dinner", "lunch",
    ]

    def __init__(self):
        self.location_kws = [k.lower() for k in self.LOCATION_KEYWORDS]
        self.announce_kws = [k.lower() for k in self.ANNOUNCEMENT_KEYWORDS]

    def matches(self, post: Post) -> bool:
        text = post.text.lower()
        has_location = any(kw in text for kw in self.location_kws)
        has_announcement = any(kw in text for kw in self.announce_kws)
        # must have BOTH a location signal AND an announcement signal
        return has_location and has_announcement
    
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