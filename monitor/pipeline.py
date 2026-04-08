from .filters.basic import LengthFilter, KeywordFilter
from .filters.llm import DeepSeekFilter

class EventPipeline:
    def __init__(self):
        self.stages = [
            KeywordFilter(["event", "meetup", "party", "workshop", "join us"]),
            LengthFilter(min_length=60),
            DeepSeekFilter(mode="classify")
        ]
        self.stats = {"total": 0, "passed": 0, "cost": 0}

    def run(self, post):
        self.stats["total"] += 1
        for stage in self.stages:
            if not stage.process(post):
                return None
        
        self.stats["passed"] += 1
        # If it passes all, extract details
        self.stats["cost"] += 0.0005 # Estimate
        extractor = DeepSeekFilter(mode="extract")
        return extractor.extract(post)