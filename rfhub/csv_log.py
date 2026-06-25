import csv
import json
from datetime import datetime
from pathlib import Path

FIELDNAMES = [
    "timestamp",
    "run_id",
    "mode",
    "source",
    "sensor_id",
    "sensor_type",
    "measurement",
    "value",
    "unit",
    "frequency_hz",
    "label",
    "meta_json",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def append_rows(csv_path, rows, run_id, mode):
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = csv_path.exists()

    with csv_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)

        if not file_exists:
            writer.writeheader()

        for item in rows:
            row = {key: "" for key in FIELDNAMES}

            meta = item.pop("meta", {}) if "meta" in item else {}
            row.update(item)

            row["timestamp"] = row.get("timestamp") or now_iso()
            row["run_id"] = run_id
            row["mode"] = mode
            row["meta_json"] = json.dumps(meta, sort_keys=True)

            writer.writerow(row)
