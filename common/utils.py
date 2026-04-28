import os
import requests

def get_distance(origin, destination):
    url = os.getenv("GOOGLE_MAP_URL")

    params = {
        "origins": f"{origin['lat']},{origin['lng']}",
        "destinations": f"{destination['lat']},{destination['lng']}",
        "key": os.getenv("GOOGLE_MAP_API_KEY")
    }

    res = requests.get(url, params=params, timeout=5)
    data = res.json()

    element = data["rows"][0]["elements"][0]

    if element["status"] != "OK":
        raise Exception("Cannot calculate distance")

    return {
        "distance_m": element["distance"]["value"],
        "duration_s": element["duration"]["value"]
    }