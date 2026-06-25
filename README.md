# RF Data Hub

A Raspberry Pi-based RF and environmental data logging platform that combines RTL-SDR signal measurements, local sensor readings, public weather API data, clean CSV export, and a local FastAPI dashboard.

## Overview

RF Data Hub is designed to make local radio-frequency data easier to collect, organize, and share. The project uses a Raspberry Pi with an RTL-SDR receiver to measure relative RF power across user-defined frequencies. It also logs environmental and system data such as pressure, weather conditions, CPU temperature, disk usage, and uptime.

The goal is to create a low-cost, configurable platform for building open RF datasets. Many useful RF measurements are local, time-dependent, and hard to find in public datasets. This project makes it possible to collect those measurements over time and pair them with environmental context.

## Features

* RTL-SDR-based RF power measurements
* Single-frequency monitoring mode
* Multi-frequency sweep mode
* Configurable frequency list
* User-editable YAML config file
* Modular sensor system
* Five default data sources:

  * SparkFun Qwiic MicroPressure sensor
  * Open-Meteo weather API
  * Raspberry Pi CPU temperature
  * Raspberry Pi disk usage
  * Raspberry Pi uptime
* Clean long-format CSV logging
* Local FastAPI web dashboard
* CSV download endpoint
* JSON API endpoint for latest readings
* Mock RF mode for testing without SDR hardware
* Designed for Raspberry Pi field data collection

## Why This Project Exists

RF data is highly dependent on location, time, hardware setup, weather, antennas, and surrounding interference. While there are many tools for viewing radio spectrum data live, there are fewer beginner-friendly systems for logging structured RF measurements over time.

RF Data Hub was built to create a simple and extendable way to collect local RF observations and pair them with environmental data. The project is intended for learning, experimentation, portfolio development, and future expansion into open RF datasets.

## Hardware Used

Current test setup:

* Raspberry Pi 3B / Pi Zero-compatible Linux setup
* RTL-SDR receiver
* SparkFun Qwiic MicroPressure sensor
* Ethernet or Wi-Fi connection
* Optional sensors through future config extensions

## Software Stack

* Python
* RTL-SDR command-line tools
* `rtl_power`
* FastAPI
* Uvicorn
* PyYAML
* Requests
* SparkFun Qwiic MicroPressure Python library
* Open-Meteo weather API
* CSV-based data logging

## Project Structure

```text
rf-data-hub/
├── rfhub/
│   ├── __init__.py
│   ├── app.py          # FastAPI web dashboard and API
│   ├── config.py       # YAML config loading
│   ├── csv_log.py      # CSV writing utilities
│   ├── main.py         # Main logger runtime
│   ├── sdr.py          # RTL-SDR measurement logic
│   └── sensors.py      # Modular sensor system
├── config.example.yaml # Example user configuration
├── .gitignore
└── README.md
```

## Data Format

RF Data Hub uses a long-format CSV so that new sensors can be added without changing the entire file structure.

Example columns:

```text
timestamp,run_id,mode,source,sensor_id,sensor_type,measurement,value,unit,frequency_hz,label,meta_json
```

Example rows:

```text
2026-06-25T12:30:00,20260625_123000,monitor,rtl_sdr,rtl_sdr,rf_power,rf_power_avg_dbfs,-42.7,dBFS,162550000,NOAA Weather Radio,{}
2026-06-25T12:30:00,20260625_123000,monitor,local_sensor,sparkfun_pressure,sparkfun_micropressure,pressure_hpa,1009.1,hPa,,,
2026-06-25T12:30:00,20260625_123000,monitor,weather_api,open_meteo_weather,open_meteo_current,temperature_2m,27.4,°C,,,
```

## Modes

### Monitor Mode

Monitor mode tracks one frequency for a defined amount of time at a defined interval.

Example use cases:

* NOAA Weather Radio signal strength over time
* Local FM broadcast monitoring
* Ham repeater activity
* ADS-B band noise floor tracking
* Long-term RF stability testing

### Sweep Mode

Sweep mode scans a user-defined list of frequencies. The user can set the number of sweep repeats or run continuously.

Example use cases:

* Comparing activity across several bands
* Building a local RF environment profile
* Logging common signals throughout the day
* Tracking band occupancy trends

## Configuration

The project is controlled using `config.yaml`.

A public-safe example is provided as:

```text
config.example.yaml
```

To use it:

```bash
cp config.example.yaml config.yaml
```

Then edit:

```bash
nano config.yaml
```

Important settings include:

```yaml
rf:
  enabled: true
  mock: false
  mode: "monitor"
```

For single-frequency monitoring:

```yaml
monitor:
  label: "NOAA Weather Radio"
  frequency_hz: 162550000
  duration_s: 300
  interval_s: 10
```

For sweep mode:

```yaml
sweep:
  repeats: 1
  frequencies:
    - label: "FM Broadcast Example"
      frequency_hz: 100100000
    - label: "NOAA Weather Radio"
      frequency_hz: 162550000
    - label: "ADS-B 1090 MHz"
      frequency_hz: 1090000000
```

## Installation

Install system dependencies:

```bash
sudo apt update
sudo apt install -y rtl-sdr python3-pip python3-venv i2c-tools
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python packages:

```bash
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn pyyaml requests sparkfun-qwiic-micropressure
```

## Running the Logger

```bash
cd ~/projects/rf-data-hub
source .venv/bin/activate
python -m rfhub.main
```

The logger writes data to:

```text
data/readings.csv
```

## Running the Dashboard

In a second terminal:

```bash
cd ~/projects/rf-data-hub
source .venv/bin/activate
uvicorn rfhub.app:app --host 0.0.0.0 --port 8000
```

Then open the dashboard from another computer on the same network:

```text
http://<pi-ip>:8000
```

Useful endpoints:

```text
/                 Web dashboard
/api/latest       Latest readings as JSON
/api/export       Download CSV file
```

## Notes on RF Measurements

The RTL-SDR measurements are relative power measurements, not calibrated laboratory-grade dBm readings. They are still useful for observing trends, comparing frequencies, identifying activity, and logging changes over time.

For calibrated RF measurements, the system would need additional calibration steps, known references, and controlled RF hardware.

## Future Improvements

Planned or possible extensions:

* SQLite database backend
* Plotting and historical charts in the dashboard
* GPS module support
* Light sensor support through an ADC
* ADS-B aircraft count integration
* Solar and geomagnetic index API logging
* Automatic scheduled runs
* Sensor plugin interface
* Multi-node RF data collection
* Public dataset export tools

## Project Goal

RF Data Hub is intended to be a low-cost platform for collecting useful local RF data. It combines radio measurements, environmental context, and open data tools into a system that can grow from a simple Raspberry Pi logger into a larger RF observatory project.
