import time
from datetime import datetime

from rfhub.config import load_config, csv_path_from_config
from rfhub.csv_log import append_rows
from rfhub.sensors import build_sensors, read_all_sensors
from rfhub.sdr import measure_frequency


def print_rows(rows):
    for row in rows:
        measurement = row.get("measurement", "")
        value = row.get("value", "")
        unit = row.get("unit", "")
        label = row.get("label", "")
        freq = row.get("frequency_hz", "")

        if freq:
            print(f"{measurement}: {value} {unit} @ {freq} Hz {label}")
        else:
            print(f"{measurement}: {value} {unit}")


def run_monitor(config, sensors, csv_path, run_id):
    rf_config = config.get("rf", {})
    monitor_cfg = rf_config.get("monitor", {})

    label = monitor_cfg.get("label", "monitor")
    frequency_hz = int(monitor_cfg.get("frequency_hz"))
    duration_s = int(monitor_cfg.get("duration_s", 300))
    interval_s = int(monitor_cfg.get("interval_s", 10))

    print(f"RF monitor mode: {label} at {frequency_hz} Hz")
    print(f"Duration: {duration_s}s | Interval: {interval_s}s")

    end_time = time.time() + duration_s

    while time.time() < end_time:
        cycle_start = time.time()

        rows = []
        rows.extend(measure_frequency(frequency_hz, label, rf_config))
        rows.extend(read_all_sensors(sensors))

        append_rows(csv_path, rows, run_id, "monitor")
        print_rows(rows)
        print("-" * 50)

        elapsed = time.time() - cycle_start
        sleep_s = max(0, interval_s - elapsed)
        time.sleep(sleep_s)


def run_sweep(config, sensors, csv_path, run_id):
    rf_config = config.get("rf", {})
    sweep_cfg = rf_config.get("sweep", {})

    repeats = int(sweep_cfg.get("repeats", 1))
    frequencies = sweep_cfg.get("frequencies", [])

    if not frequencies:
        print("No sweep frequencies configured.")
        return

    print(f"RF sweep mode with {len(frequencies)} frequencies")
    print(f"Repeats: {repeats}")

    repeat_counter = 0

    while repeats == 0 or repeat_counter < repeats:
        repeat_counter += 1
        print(f"Starting sweep repeat {repeat_counter}")

        for item in frequencies:
            label = item.get("label", "sweep")
            frequency_hz = int(item.get("frequency_hz"))

            rows = []
            rows.extend(measure_frequency(frequency_hz, label, rf_config))
            rows.extend(read_all_sensors(sensors))

            append_rows(csv_path, rows, run_id, "sweep")
            print_rows(rows)
            print("-" * 50)


def main():
    config = load_config()
    csv_path = csv_path_from_config(config)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"Starting {config['project'].get('name', 'RF Data Hub')}")
    print(f"Run ID: {run_id}")
    print(f"CSV: {csv_path}")

    sensors = build_sensors(config)

    rf_config = config.get("rf", {})
    mode = rf_config.get("mode", "monitor")

    try:
        if not rf_config.get("enabled", True):
            print("RF disabled. Logging sensors only.")
            while True:
                rows = read_all_sensors(sensors)
                append_rows(csv_path, rows, run_id, "sensors_only")
                print_rows(rows)
                print("-" * 50)
                time.sleep(10)

        elif mode == "monitor":
            run_monitor(config, sensors, csv_path, run_id)

        elif mode == "sweep":
            run_sweep(config, sensors, csv_path, run_id)

        else:
            print(f"Unknown RF mode: {mode}")

    except KeyboardInterrupt:
        print("Stopped by user.")


if __name__ == "__main__":
    main()
