import csv
from collections import deque
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from rfhub.config import load_config, csv_path_from_config

app = FastAPI(title="RF Data Hub")

config = load_config()
csv_path = csv_path_from_config(config)


def read_recent_rows(limit=100):
    path = Path(csv_path)

    if not path.exists():
        return []

    rows = deque(maxlen=limit)

    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return list(rows)


@app.get("/", response_class=HTMLResponse)
def home():
    name = config["project"].get("name", "RF Data Hub")

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 30px;
            background: #111;
            color: #eee;
        }}
        h1 {{
            margin-bottom: 0;
        }}
        .subtitle {{
            color: #aaa;
            margin-top: 4px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
            font-size: 14px;
        }}
        th, td {{
            border: 1px solid #333;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background: #222;
        }}
        tr:nth-child(even) {{
            background: #181818;
        }}
        a {{
            color: #8ab4ff;
        }}
        .card {{
            background: #181818;
            border: 1px solid #333;
            padding: 15px;
            margin-top: 20px;
            border-radius: 10px;
        }}
    </style>
</head>
<body>
    <h1>{name}</h1>
    <p class="subtitle">Raspberry Pi RF + sensor + weather data logger</p>

    <div class="card">
        <p><b>CSV file:</b> {csv_path}</p>
        <p>
            <a href="/api/latest?limit=50">Latest JSON</a> |
            <a href="/api/export">Download CSV</a>
        </p>
    </div>

    <h2>Latest readings</h2>
    <table id="data-table">
        <thead>
            <tr>
                <th>Time</th>
                <th>Source</th>
                <th>Sensor</th>
                <th>Measurement</th>
                <th>Value</th>
                <th>Unit</th>
                <th>Freq Hz</th>
                <th>Label</th>
            </tr>
        </thead>
        <tbody></tbody>
    </table>

<script>
async function loadData() {{
    const response = await fetch('/api/latest?limit=100');
    const data = await response.json();
    const tbody = document.querySelector('#data-table tbody');
    tbody.innerHTML = '';

    data.rows.reverse().forEach(row => {{
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${{row.timestamp || ''}}</td>
            <td>${{row.source || ''}}</td>
            <td>${{row.sensor_id || ''}}</td>
            <td>${{row.measurement || ''}}</td>
            <td>${{row.value || ''}}</td>
            <td>${{row.unit || ''}}</td>
            <td>${{row.frequency_hz || ''}}</td>
            <td>${{row.label || ''}}</td>
        `;
        tbody.appendChild(tr);
    }});
}}

loadData();
setInterval(loadData, 5000);
</script>
</body>
</html>
"""


@app.get("/api/latest")
def latest(limit: int = Query(100, ge=1, le=5000)):
    return {"rows": read_recent_rows(limit)}


@app.get("/api/export")
def export_csv():
    path = Path(csv_path)

    if not path.exists():
        return JSONResponse({"error": "CSV does not exist yet. Start the logger first."}, status_code=404)

    return FileResponse(path, filename=path.name, media_type="text/csv")
