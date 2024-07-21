from multion.client import MultiOn

client = MultiOn(
    api_key="27e7159454bf421ea97d7ce085cddb14",
)

retrieve_response = client.retrieve(
    cmd="Using wikipidia, tell me if a lion is a reptile",
    url="https://www.wikipedia.org/",
    fields=["objective", "explanation"]
)

data = retrieve_response.data[0]["explanation"]
print(data)
