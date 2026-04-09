from .filters.basic import MetadataFilter, LengthFilter, ProfanityFilter
from .filters.llm import LLMClassifyStage, LLMExtractStage

# --- Cost estimation constants ---
# DeepSeek V3.2 pricing:
#   Input:  2 RMB / 7 = ~$0.29 per million tokens
#   Output: 3 RMB / 7 = ~$0.43 per million tokens
AVG_CLASSIFY_IN  = 150   # prompt + post text
AVG_CLASSIFY_OUT = 5     # "Yes" or "No"
AVG_EXTRACT_IN   = 180
AVG_EXTRACT_OUT  = 100   # JSON with 4 fields

USD_PER_M_IN  = 2.0 / 7
USD_PER_M_OUT = 3.0 / 7


class EventPipeline:
    """
    The pipeline is just an ordered list of Stage objects.
    To add, remove, or reorder stages — only edit the list in __init__.
    Nothing else needs to change.
    """
    def __init__(self):
        self.stages: list = [
            MetadataFilter(),
            LengthFilter(min_length=60, max_length=500),
            ProfanityFilter(),
            LLMClassifyStage(),
        ]
        self.extractor = LLMExtractStage()
        self.reset_stats()

    def reset_stats(self):
        self.stats = {
            "total": 0,
            "per_stage": [0] * len(self.stages),
            "passed": 0,
        }

    def run(self, post):
        """
        Pass a post through every stage in order.
        Returns extracted event dict if all stages pass, else None.
        """
        self.stats["total"] += 1
        for i, stage in enumerate(self.stages):
            if not stage.matches(post):
                return None
            self.stats["per_stage"][i] += 1
        self.stats["passed"] += 1
        return self.extractor.extract(post)

    def estimate_cost(self):
        """
        Estimate cost from post counts × average token estimates.
        Posts that reach LLMClassifyStage = passed profanity filter (stage index 2).
        Posts that reach LLMExtractStage  = self.stats['passed'].
        """
        reaching_classify = self.stats["per_stage"][2] if len(self.stages) > 2 else 0
        reaching_extract  = self.stats["passed"]

        in_tokens  = (reaching_classify * AVG_CLASSIFY_IN +
                      reaching_extract  * AVG_EXTRACT_IN)
        out_tokens = (reaching_classify * AVG_CLASSIFY_OUT +
                      reaching_extract  * AVG_EXTRACT_OUT)

        cost_usd = (in_tokens  / 1_000_000 * USD_PER_M_IN +
                    out_tokens / 1_000_000 * USD_PER_M_OUT)
        return cost_usd

    def get_stats_dict(self):
        """Flat dict suitable for one row in the eval CSV log."""
        cost_usd = self.estimate_cost()
        total  = self.stats["total"]
        passed = self.stats["passed"]
        d = {
            "total": total,
            "passed": passed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "cost_usd": round(cost_usd, 6),
        }
        for i, stage in enumerate(self.stages):
            d[f"{stage.name}_out"] = self.stats["per_stage"][i]
        return d

    def print_stats(self):
        total  = self.stats["total"]
        passed = self.stats["passed"]
        cost_usd = self.estimate_cost()

        print(f"\n--- Pipeline Stats ---")
        print(f"{'Stage':<20} {'In':>6} {'Out':>6} {'Dropped':>8}")
        print("-" * 44)
        prev = total
        for i, stage in enumerate(self.stages):
            out     = self.stats["per_stage"][i]
            dropped = prev - out
            print(f"{stage.name:<20} {prev:>6} {out:>6} {dropped:>8}")
            prev = out
        print(f"{'llm_extract':<20} {prev:>6} {passed:>6} {prev - passed:>8}")
        print("-" * 44)
        print(f"{'TOTAL':<20} {total:>6} {passed:>6} {total - passed:>8}")
        print(f"\nPass rate     : {passed/total*100:.1f}%" if total > 0 else "")
        print(f"Estimated cost: ${cost_usd:.6f} USD")