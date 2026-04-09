# test_one.py  (in your project root)
from monitor.filters.base import Post
from monitor.pipeline import EventPipeline

pipeline = EventPipeline()
post = Post(
    id="test1",
    text="Join us Saturday at Balboa Park for a community meetup! Bring friends, 2pm start.",
    author="testuser",
    created_at="now",
    raw_data={}
)
result = pipeline.run(post)
print("Result:", result)
pipeline.print_stats()