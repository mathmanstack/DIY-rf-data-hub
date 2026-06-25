import time
import qwiic_micropressure

sensor = qwiic_micropressure.QwiicMicroPressure()

if not sensor.connected:
    print("Pressure sensor not detected. Check wiring and run: i2cdetect -y 1")
    raise SystemExit

sensor.begin()

print("Pressure sensor running. Press Ctrl+C to stop.")

while True:
    pressure_psi = sensor.read_pressure()
    pressure_kpa = pressure_psi * 6.89476
    pressure_hpa = pressure_kpa * 10

    print(f"{pressure_psi:.3f} psi | {pressure_kpa:.2f} kPa | {pressure_hpa:.1f} hPa")
    time.sleep(1)
