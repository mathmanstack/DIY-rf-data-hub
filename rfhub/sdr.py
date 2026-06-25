import csv
import os
import random
import shutil
import subprocess
import tempfile


def _mock_rf_reading(center_hz, label):
    avg = random.uniform(-65, -35)
    peak = avg + random.uniform(1, 8)

    return [
        {
            "source": "rtl_sdr",
            "sensor_id": "rtl_sdr",
            "sensor_type": "rf_power",
            "measurement": "rf_power_avg_dbfs",
            "value": round(avg, 2),
            "unit": "dBFS",
            "frequency_hz": int(center_hz),
            "label": label,
            "meta": {"mock": True},
        },
        {
            "source": "rtl_sdr",
            "sensor_id": "rtl_sdr",
            "sensor_type": "rf_power",
            "measurement": "rf_power_peak_dbfs",
            "value": round(peak, 2),
            "unit": "dBFS",
            "frequency_hz": int(center_hz),
            "label": label,
            "meta": {"mock": True},
        },
    ]


def _parse_rtl_power_csv(path):
    db_values = []

    with open(path, "r", newline="") as f:
        reader = csv.reader(f)

        for row in reader:
            if len(row) < 7:
                continue

            for item in row[6:]:
                try:
                    db_values.append(float(item))
                except ValueError:
                    pass

    if not db_values:
        return None, None, 0

    avg = sum(db_values) / len(db_values)
    peak = max(db_values)

    return avg, peak, len(db_values)


def measure_frequency(center_hz, label, rf_config):
    center_hz = int(center_hz)

    if rf_config.get("mock", False):
        return _mock_rf_reading(center_hz, label)

    if shutil.which("rtl_power") is None:
        return [
            {
                "source": "rtl_sdr",
                "sensor_id": "rtl_sdr",
                "sensor_type": "rf_power",
                "measurement": "rtl_power_missing",
                "value": "",
                "unit": "",
                "frequency_hz": center_hz,
                "label": label,
                "meta": {"error": "rtl_power command not found. Install with: sudo apt install rtl-sdr"},
            }
        ]

    span_hz = int(rf_config.get("span_hz", 200000))
    bin_hz = int(rf_config.get("bin_hz", 25000))
    dwell_s = max(1, int(rf_config.get("dwell_s", 2)))
    gain = rf_config.get("gain", "auto")

    low_hz = center_hz - span_hz // 2
    high_hz = center_hz + span_hz // 2

    fd, temp_path = tempfile.mkstemp(prefix="rtl_power_", suffix=".csv")
    os.close(fd)
    os.remove(temp_path)

    cmd = [
        "rtl_power",
        "-f",
        f"{low_hz}:{high_hz}:{bin_hz}",
        "-i",
        f"{dwell_s}s",
        "-e",
        f"{dwell_s}s",
    ]

    if str(gain).lower() != "auto":
        cmd.extend(["-g", str(gain)])

    cmd.append(temp_path)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=dwell_s + 20,
        )

        if result.returncode != 0:
            return [
                {
                    "source": "rtl_sdr",
                    "sensor_id": "rtl_sdr",
                    "sensor_type": "rf_power",
                    "measurement": "rtl_power_error",
                    "value": "",
                    "unit": "",
                    "frequency_hz": center_hz,
                    "label": label,
                    "meta": {
                        "cmd": " ".join(cmd),
                        "stderr": result.stderr.strip(),
                    },
                }
            ]

        avg, peak, bins = _parse_rtl_power_csv(temp_path)

        if avg is None:
            return [
                {
                    "source": "rtl_sdr",
                    "sensor_id": "rtl_sdr",
                    "sensor_type": "rf_power",
                    "measurement": "rtl_power_no_data",
                    "value": "",
                    "unit": "",
                    "frequency_hz": center_hz,
                    "label": label,
                    "meta": {"cmd": " ".join(cmd)},
                }
            ]

        return [
            {
                "source": "rtl_sdr",
                "sensor_id": "rtl_sdr",
                "sensor_type": "rf_power",
                "measurement": "rf_power_avg_dbfs",
                "value": round(avg, 2),
                "unit": "dBFS",
                "frequency_hz": center_hz,
                "label": label,
                "meta": {
                    "span_hz": span_hz,
                    "bin_hz": bin_hz,
                    "dwell_s": dwell_s,
                    "bins": bins,
                    "gain": gain,
                },
            },
            {
                "source": "rtl_sdr",
                "sensor_id": "rtl_sdr",
                "sensor_type": "rf_power",
                "measurement": "rf_power_peak_dbfs",
                "value": round(peak, 2),
                "unit": "dBFS",
                "frequency_hz": center_hz,
                "label": label,
                "meta": {
                    "span_hz": span_hz,
                    "bin_hz": bin_hz,
                    "dwell_s": dwell_s,
                    "bins": bins,
                    "gain": gain,
                },
            },
        ]

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
