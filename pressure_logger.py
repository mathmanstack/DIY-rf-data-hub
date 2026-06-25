import csv
import time
from datetime import datetime
from pathlib import Path

import qwiic_micropressure

LOG_FILE = Path("pressure_log.csv")
SAMPLE_DELAY_S = 1.0

sensor = qwiic_micropressure.QwiicMicroPressure()

if not sensor.is_connected():
    print("Sensor not detected. Run: i2cdetect -y 1")
    raise SystemExit

sensor.begin()

if not LOG_FILE.exists():
    with LOG_FILE.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "pressure_psi",
            "pressure_kpa",
            "pressure_hpa"
        ])

print("Pressure logger running. Press Ctrl+C to stop.")
print(f"Saving to: {LOG_FILE.resolve()}")

while True:
    timestamp = datetime.now().isoformat(timespec="seconds")

    pressure_psi = sensor.read_pressure()
    pressure_kpa = pressure_psi * 6.89476
    pressure_hpa = pressure_kpa * 10.0

    with LOG_FILE.open("a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            round(pressure_psi, 4),
            round(pressure_kpa, 3),
            round(pressure_hpa, 2)
        ])

    print(f"{timestamp} | {pressure_psi:.3f} psi | {pressure_hpa:.1f} hPa")

    time.sleep(SAMPLE_DELAY_S)

