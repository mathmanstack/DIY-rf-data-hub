import os
import shutil
import time
from pathlib import Path

import requests


class BaseSensor:
    def __init__(self, sensor_id, cfg, global_config):
        self.sensor_id = sensor_id
        self.cfg = cfg
        self.global_config = global_config

    def read(self):
        return []


class SparkFunMicroPressureSensor(BaseSensor):
    def __init__(self, sensor_id, cfg, global_config):
        super().__init__(sensor_id, cfg, global_config)

        import qwiic_micropressure

        self.sensor = qwiic_micropressure.QwiicMicroPressure()

        is_connected = (
            self.sensor.is_connected()
            if hasattr(self.sensor, "is_connected")
            else self.sensor.connected
        )

        if not is_connected:
            raise RuntimeError("SparkFun MicroPressure sensor not detected at I2C address 0x18")

        self.sensor.begin()

    def read(self):
        psi = float(self.sensor.read_pressure())
        kpa = psi * 6.89476
        hpa = kpa * 10.0

        return [
            {
                "source": "local_sensor",
                "sensor_id": self.sensor_id,
                "sensor_type": "sparkfun_micropressure",
                "measurement": "pressure_psi",
                "value": round(psi, 4),
                "unit": "psi",
            },
            {
                "source": "local_sensor",
                "sensor_id": self.sensor_id,
                "sensor_type": "sparkfun_micropressure",
                "measurement": "pressure_kpa",
                "value": round(kpa, 3),
                "unit": "kPa",
            },
            {
                "source": "local_sensor",
                "sensor_id": self.sensor_id,
                "sensor_type": "sparkfun_micropressure",
                "measurement": "pressure_hpa",
                "value": round(hpa, 2),
                "unit": "hPa",
            },
        ]


class OpenMeteoCurrentWeatherSensor(BaseSensor):
    def __init__(self, sensor_id, cfg, global_config):
        super().__init__(sensor_id, cfg, global_config)
        self.interval_s = int(cfg.get("interval_s", 300))
        self.last_fetch = 0

    def read(self):
        now = time.time()

        if now - self.last_fetch < self.interval_s:
            return []

        self.last_fetch = now

        loc = self.global_config.get("location", {})
        latitude = loc.get("latitude")
        longitude = loc.get("longitude")

        if latitude is None or longitude is None:
            return []

        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "pressure_msl",
                    "surface_pressure",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "precipitation",
                ]
            ),
            "timezone": "auto",
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            return [
                {
                    "source": "weather_api",
                    "sensor_id": self.sensor_id,
                    "sensor_type": "open_meteo_current",
                    "measurement": "weather_api_error",
                    "value": "",
                    "unit": "",
                    "meta": {"error": str(e)},
                }
            ]

        current = data.get("current", {})
        units = data.get("current_units", {})

        rows = []

        for key, value in current.items():
            if key == "time":
                continue

            rows.append(
                {
                    "source": "weather_api",
                    "sensor_id": self.sensor_id,
                    "sensor_type": "open_meteo_current",
                    "measurement": key,
                    "value": value,
                    "unit": units.get(key, ""),
                    "meta": {
                        "location_name": loc.get("name", ""),
                        "latitude": latitude,
                        "longitude": longitude,
                        "weather_time": current.get("time", ""),
                    },
                }
            )

        return rows


class PiCpuTempSensor(BaseSensor):
    def read(self):
        path = Path("/sys/class/thermal/thermal_zone0/temp")

        if not path.exists():
            return []

        temp_c = int(path.read_text().strip()) / 1000.0

        return [
            {
                "source": "system",
                "sensor_id": self.sensor_id,
                "sensor_type": "pi_cpu_temp",
                "measurement": "pi_cpu_temp_c",
                "value": round(temp_c, 2),
                "unit": "C",
            }
        ]


class SystemDiskSensor(BaseSensor):
    def read(self):
        usage = shutil.disk_usage("/")
        used_pct = usage.used / usage.total * 100.0

        return [
            {
                "source": "system",
                "sensor_id": self.sensor_id,
                "sensor_type": "system_disk",
                "measurement": "disk_used_percent",
                "value": round(used_pct, 2),
                "unit": "%",
            },
            {
                "source": "system",
                "sensor_id": self.sensor_id,
                "sensor_type": "system_disk",
                "measurement": "disk_free_gb",
                "value": round(usage.free / 1e9, 3),
                "unit": "GB",
            },
        ]


class SystemUptimeSensor(BaseSensor):
    def read(self):
        try:
            with open("/proc/uptime", "r") as f:
                uptime_s = float(f.read().split()[0])
        except Exception:
            return []

        return [
            {
                "source": "system",
                "sensor_id": self.sensor_id,
                "sensor_type": "system_uptime",
                "measurement": "uptime_s",
                "value": round(uptime_s, 1),
                "unit": "s",
            }
        ]


SENSOR_TYPES = {
    "sparkfun_micropressure": SparkFunMicroPressureSensor,
    "open_meteo_current": OpenMeteoCurrentWeatherSensor,
    "pi_cpu_temp": PiCpuTempSensor,
    "system_disk": SystemDiskSensor,
    "system_uptime": SystemUptimeSensor,
}


def build_sensors(config):
    sensors = []

    for sensor_cfg in config.get("sensors", []):
        if not sensor_cfg.get("enabled", True):
            continue

        sensor_type = sensor_cfg.get("type")
        sensor_id = sensor_cfg.get("id", sensor_type)

        cls = SENSOR_TYPES.get(sensor_type)

        if cls is None:
            print(f"Unknown sensor type in config: {sensor_type}")
            continue

        try:
            sensor = cls(sensor_id, sensor_cfg, config)
            sensors.append(sensor)
            print(f"Loaded sensor: {sensor_id} ({sensor_type})")
        except Exception as e:
            print(f"Failed to load sensor {sensor_id} ({sensor_type}): {e}")

    return sensors


def read_all_sensors(sensors):
    rows = []

    for sensor in sensors:
        try:
            rows.extend(sensor.read())
        except Exception as e:
            rows.append(
                {
                    "source": "sensor_error",
                    "sensor_id": getattr(sensor, "sensor_id", "unknown"),
                    "sensor_type": sensor.__class__.__name__,
                    "measurement": "sensor_read_error",
                    "value": "",
                    "unit": "",
                    "meta": {"error": str(e)},
                }
            )

    return rows
