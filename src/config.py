import json
from pathlib import Path
import os

# Get the directory containing this script (src/)
current_dir = Path(__file__).parent.absolute()
config_path = current_dir / "config.json"

def load_config():
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback defaults if config.json is missing
        return {
            "data_dir": "data",
            "storage_base": "storage"
        }

config = load_config()
