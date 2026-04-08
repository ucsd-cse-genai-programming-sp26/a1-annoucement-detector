from dataclasses import dataclass
from typing import Optional

@dataclass
class Post:
    id: str
    text: str
    author: str
    created_at: str
    raw_data: dict

class BaseFilter:
    def process(self, post: Post) -> bool:
        raise NotImplementedError