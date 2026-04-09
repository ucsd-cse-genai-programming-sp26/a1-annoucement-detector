from dataclasses import dataclass

@dataclass
class Post:
    id: str
    text: str
    author: str
    created_at: str
    raw_data: dict

class Stage:
    """
    Base class for all pipeline stages.
    Every stage answers one question: should this post continue?
    Subclasses must set a name and implement matches().
    """
    name: str = "unnamed"

    def matches(self, post: Post) -> bool:
        raise NotImplementedError(f"Stage '{self.name}' must implement matches()")

    def __repr__(self):
        return f"<Stage: {self.name}>"