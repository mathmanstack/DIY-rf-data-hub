from pathlib import Path
import yaml

def load_config(path="config.yaml"):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")

    with path.open("r") as f:
        return yaml.safe_load(f)

def csv_path_from_config(config):
    data_dir = config["project"].get("data_dir", "data")
    csv_file = config["project"].get("csv_file", "readings.csv")
    return Path(data_dir) / csv_file
