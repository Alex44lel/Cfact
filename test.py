from multion.client import MultiOn

client = MultiOn(
    api_key="27e7159454bf421ea97d7ce085cddb14",
)

retrieve_response = client.retrieve(
    cmd="Get all posts on Hackernews with title, creator, time created, points as a number, number of comments as a number, and the post URL.",
    url="https://news.ycombinator.com/",
    fields=["title", "creator", "time", "points", "comments", "url"]
)

data = retrieve_response.data
print(data)