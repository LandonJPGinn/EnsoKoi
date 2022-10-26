import json
from pathlib import Path


def initial_positions(key):
    path = Path(".").resolve() / "config" / "initial_positions.json"
    with open(path, "r") as f:
        data = json.load(f)
    return data.get(key)
