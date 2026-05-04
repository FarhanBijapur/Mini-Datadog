# Mini Datadog

Mini Datadog is a local observability demo platform with real-time log ingestion, in-memory metrics aggregation, MongoDB persistence, anomaly detection, and a dark React dashboard inspired by Datadog/Grafana.

## Current State

The project currently includes:

- FastAPI backend for log ingestion and metrics APIs.
- MongoDB-backed log storage.
- In-memory queue for ingestion buffering and backpressure simulation.
- Background worker for batch processing and persistence.
- Sliding-window error analytics.
- Rule-based anomaly detection.
- React + Tailwind CSS frontend dashboard.
- Chart.js visualizations for error trend and logs per service.
- Real recent-log table powered by `GET /logs`.
- Demo traffic generator for showing the dashboard with real ingested data.

No fake frontend fallback data is used. If the backend is offline, the dashboard shows offline/empty states.

## Tech Stack

Backend:

- Python
- FastAPI
- Uvicorn
- PyMongo
- MongoDB
- asyncio/threading

Frontend:

- React
- Vite
- Tailwind CSS
- Chart.js
- react-chartjs-2
- Axios

## Architecture

```text
POST /logs
   |
   v
FastAPI validation
   |
   v
In-memory ingestion queue
   |
   v
Background worker
   |
   v
Processing engine + anomaly detection
   |
   v
MongoDB log storage
```

Dashboard polling:

```text
React dashboard
   |
   +--> GET /metrics every 3 seconds
   |
   +--> GET /logs every 3 seconds
```

## Backend API

### Health Check

```http
GET /healthz
```

Returns:

```json
{
  "status": "ok"
}
```

### Ingest Log

```http
POST /logs
```

Example payload:

```json
{
  "source": "demo-generator",
  "service": "checkout-api",
  "level": "ERROR",
  "message": "payment authorization failed",
  "attributes": {
    "region": "ap-south-1",
    "latency_ms": 420
  },
  "tags": ["demo", "local"]
}
```

Returns `202 Accepted` when the event is queued.

### Recent Logs

```http
GET /logs?limit=50
```

Returns recent persisted logs from MongoDB:

```json
{
  "logs": []
}
```

`limit` supports values from `1` to `200`.

### Metrics

```http
GET /metrics
```

Returns:

- System throughput counters.
- Queue depth and worker status.
- Error analytics.
- Logs per service.
- Error count per service.
- Frequency by service/level.
- Anomaly state.

## Run Locally

### 1. Start MongoDB

MongoDB must be running on:

```text
mongodb://localhost:27017
```

The backend uses database `mini_datadog` and collection `logs` by default.

### 2. Install Backend Dependencies

From the project root:

```powershell
cd "D:\Mini Datadog"
pip install -r requirements.txt
```

### 3. Start Backend

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Backend docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/healthz
```

### 4. Install Frontend Dependencies

From the frontend folder:

```powershell
cd "D:\Mini Datadog\frontend"
npm install
```

### 5. Start Frontend

```powershell
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

## Demo Workflow

Use the demo traffic generator to send real log events into the backend.

Normal traffic:

```powershell
cd "D:\Mini Datadog"
python scripts\generate_demo_traffic.py --count 80 --delay 0.03
```

Error-heavy spike:

```powershell
python scripts\generate_demo_traffic.py --count 40 --delay 0.02 --spike
```

The dashboard refreshes every 3 seconds. You should see:

- Total Logs increase.
- Error Count increase.
- Error Rate update.
- Queue Depth change briefly during ingestion.
- Error trend line update.
- Logs per service bar chart update.
- Recent logs table populate from MongoDB.

Anomaly detection may not activate immediately. The current rule requires the current error window to be more than 2x the previous window, and the previous window must be greater than zero.

## Frontend Dashboard

The dashboard includes:

- Fixed dark sidebar navigation.
- Top KPI cards:
  - Total Logs
  - Error Count
  - Error Rate
  - Queue Depth
- Side-by-side charts:
  - Error Trend
  - Logs per Service
- Bottom operational panels:
  - Recent Logs
  - Anomaly Panel

The dashboard reads from:

```text
http://localhost:8000/metrics
http://localhost:8000/logs
```

## Useful Commands

Frontend lint:

```powershell
cd "D:\Mini Datadog\frontend"
npm run lint
```

Frontend production build:

```powershell
npm run build
```

Python syntax check:

```powershell
cd "D:\Mini Datadog"
python -m py_compile routes\logs.py services\storage_service.py scripts\generate_demo_traffic.py
```

Quick API checks:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/metrics
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/logs?limit=5
```

## Notes and Limitations

- Metrics are held in memory, so counters reset when the backend restarts.
- The queue is in memory and simulates a broker; Kafka/RabbitMQ would be a production replacement.
- MongoDB stores processed logs, but metrics are served from pre-aggregated in-memory state for low latency.
- Dedupe is best-effort and process-local.
- Anomaly detection is rule-based and intentionally simple for this demo.

## Future Improvements

- Replace in-memory queue with Kafka.
- Add persistent metrics time-series storage.
- Add dashboard filters by service, level, and time range.
- Add WebSocket/SSE streaming instead of polling.
- Add Docker Compose for MongoDB, backend, and frontend.
- Add automated backend tests and frontend component tests.
- Add richer statistical anomaly detection such as moving average, z-score, or EWMA.
