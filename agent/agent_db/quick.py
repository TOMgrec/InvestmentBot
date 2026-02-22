import json

data = json.load(open("agent/agent_db/tags.json", "r"))

for item in data:
    item["special"] = int(item["tag"] in ["DISLIKED", "LIKED", "NEUTRAL", "WATCHLIST", "PORTFOLIO", "AVOID", "FAVORITE"])

with open("agent/agent_db/tags.json", "w") as f:
    json.dump(data, f, indent=4)