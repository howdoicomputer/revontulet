#!/usr/bin/env python3

import json
import urllib.parse
import urllib.request

"""
An extremely simple client example that loads a config file
and opens a stream.
"""

config = json.load(open("client_example_config.json"))

params = urllib.parse.urlencode({
    "lat": config["latitude"],
    "lng": config["longitude"],
    "search_radius": config["search_radius"],
    "sat_color_pairs": ",".join(f"{k},{v}" for k, v in config["sat_color_pairs"].items()),
    "format": "text"
})

url = f"https://revontulet.lol/api/satellites/above/stream?{params}"

with urllib.request.urlopen(url) as response:
    for line in response:
        # write_to_lights(line.decode().strip())
        print(line.decode().strip())
