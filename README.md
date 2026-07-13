# Mini Datadog

> A FastAPI-based observability platform with executable API contracts using Specmatic.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![React](https://img.shields.io/badge/React-Frontend-61DAFB)
![MongoDB](https://img.shields.io/badge/MongoDB-Database-green)
![Specmatic](https://img.shields.io/badge/Specmatic-Contract%20Testing-orange)

Real-time log ingestion and anomaly detection platform with a queue-driven FastAPI backend, MongoDB persistence, in-memory metrics aggregation, and a React observability dashboard.

## Features

**Backend**
- Async log ingestion (`POST /logs`) with Pydantic validation and `202 Accepted` queue semantics
- Bounded in-memory queue with `429` backpressure on overflow
- Background worker with batch processing, supervisor restart, and graceful shutdown
- MongoDB persistence with startup indexes, singleton client, and transient-failure retries
- Processing engine with O(1) hashmap frequency tracking and 5-minute sliding-window error analytics
- Rule-based anomaly detection (`current_errors > 2x previous_errors`) with cooldown dedupe
- Best-effort in-memory deduplication (LRU + TTL)
- Pre-aggregated `/metrics` snapshot served without DB reads

**Frontend**
- Enterprise-style dark dashboard (sidebar, KPI cards, charts, recent logs, anomaly panel)
- Auto-refresh every 3 seconds from live backend APIs
- Chart.js visualizations: error trend line + logs-per-service bar chart
- Offline/empty states when the API is unavailable (no fake fallback data)

**Tooling**
- FastAPI-generated OpenAPI contract
- Specmatic V3 configuration
- Provider contract testing
- Externalized OpenAPI examples
- Schema resiliency testing
- API coverage reports
- HTML contract test reports
- OpenAPI export automation

## Tech Stack
| Layer | Stack |
|---|---|
| API | FastAPI, Uvicorn, Pydantic |
| Storage | MongoDB, PyMongo |
| Queue / Workers | queue.Queue, asyncio worker, batch inserts |
| Frontend | React, Vite, Tailwind CSS, Chart.js, Axios |
| Contracts & Testing | OpenAPI 3.x, Specmatic V3 |

## Project Structure

```text
Mini Datadog/
├── core/                 # config, MongoDB manager, ingestion queue
├── models/               # Pydantic request/response models
├── routes/               # /logs, /metrics, /healthz
├── services/             # worker, processing, storage, metrics, anomaly, dedupe
├── utils/
├── scripts/              # demo traffic, OpenAPI export, Specmatic helpers
├── contracts/openapi/    # exported API contract + examples
├── frontend/             # React dashboard
├── main.py
├── requirements.txt
└── system_design.md
```

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
Background worker (batch + dedupe + retries)
   |
   v
Processing engine + anomaly detection
   |
   v
MongoDB (logs collection)

React dashboard
   |
   +--> GET /metrics  (every 3s)
   +--> GET /logs     (every 3s)
```

See [system_design.md](system_design.md) for scaling strategy, trade-offs, and bottlenecks.

## Executable API Contracts

This project integrates **Specmatic** to treat the OpenAPI specification as an executable contract instead of static documentation.

The integration includes:

- Automatic OpenAPI export from FastAPI
- Provider contract verification
- Externalized OpenAPI examples
- Schema resiliency testing
- API coverage reporting
- HTML test reports
- Specmatic V3 configuration

The OpenAPI contract is generated directly from the FastAPI application and exported to:

```text
contracts/openapi/mini-datadog.openapi.json
```

This exported contract is then consumed by Specmatic for:

- Provider verification
- Mock generation
- API coverage
- Schema resiliency testing

## API

### `GET /healthz`

```json
{ "status": "ok" }
```

### `POST /logs`

Minimal payload:

```json
{
  "service": "payment-service",
  "level": "ERROR",
  "message": "Payment failed"
}
```

Full payload supports `source`, `timestamp`, `attributes`, `tags`, `trace_id`, and `span_id`.

Returns `202 Accepted`:

```json
{
  "status": "accepted",
  "queue_depth": 1
}
```

Returns `429` when the ingestion queue is full.

### `GET /logs?limit=50`

Returns recent persisted logs from MongoDB (`limit`: 1–200), ordered by `processed_at` descending:

```json
{
  "logs": []
}
```

### `GET /metrics`

Returns a structured observability snapshot:

- `system_throughput` — received/processed/failed, queue depth, worker status, rejections, dedupe, DB failures, worker restarts
- `error_analytics` — total errors, current/previous 5-minute window counts
- `service_level_insights` — logs and errors per service
- `frequency_tracking` — `(service, level)` hashmap counts
- `anomaly_detection` — `anomaly_active` and `last_anomaly`

Interactive docs: `http://127.0.0.1:8000/docs`


## Run Locally
### Prerequisites

- Python 3.11+
- Node.js 20+
- MongoDB
- Java 17+

Default MongoDB:

```text
mongodb://localhost:27017
```

### Backend

```powershell
cd "D:\Mini Datadog"
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

```bash
cd Mini\ Datadog
pip3 install -r requirements.txt
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```
```bash
cd frontend
npm install
npm run dev
```

Open: `http://127.0.0.1:5173`

Optional API override:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Demo Workflow

Generate traffic from the CLI:

```powershell
cd "D:\Mini Datadog"
python scripts\generate_demo_traffic.py --count 80 --delay 0.03
```

Trigger an error spike (may activate anomaly detection):

```powershell
python scripts\generate_demo_traffic.py --count 40 --delay 0.02 --spike
```

Anomaly rule: `current_window_errors > 2 * previous_window_errors` (requires `previous > 0`).

You can also ingest logs via Swagger UI (`/docs`) or `POST /logs` directly.

## Dashboard

The React UI includes:

- **Header** — live/disconnected status and last refresh time
- **KPI row** — Total Logs, Error Count, Error Rate, Queue Depth
- **Charts** — Error Trend (rolling window) and Logs per Service (top 8)
- **Recent Logs** — live table from `GET /logs`
- **Anomaly Panel** — active state, window comparison, worker status, last anomaly

Polling interval: **3 seconds**.


## Contract Testing with Specmatic

### Export OpenAPI Contract

```powershell
python scripts\export_openapi.py
```

Run Specmatic provider tests (backend must be running):

```powershell
.\scripts\run_specmatic_provider_tests.ps1
```

Contract files live in `contracts/openapi/`.

### Start Specmatic Mock Server

```powershell
.\scripts\start_specmatic_mock.ps1
```

The mock server starts on:

```
http://localhost:9000
```

Configure the frontend to use it by setting:

```text
VITE_API_BASE_URL=http://localhost:9000
```

### Schema Resiliency Testing

Specmatic can automatically generate valid request combinations from the OpenAPI schema to validate API behavior beyond manually written examples.

This helps uncover:

- Missing validation
- Incorrect status codes
- Contract drift
- Boundary-condition bugs

Reports are generated under:

```text
build/reports/specmatic/
```

## Development Commands

```powershell
# Frontend lint / build
cd frontend
npm run lint
npm run build

# Python syntax check
cd ..
python -m py_compile main.py routes\logs.py routes\metrics.py

# Quick API checks
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/metrics
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/logs?limit=5"
```

## Limitations

- Metrics and queue state are in-memory and reset on backend restart
- Queue is process-local (Kafka would replace this in production)
- Dedupe is best-effort and not shared across instances
- Anomaly detection is rule-based (no seasonality or statistical modeling yet)
- Dashboard polls REST endpoints (no WebSocket/SSE streaming)

## Future Improvements

- Increase API coverage close to 100%
- Add more external OpenAPI examples
- Enable full Schema Resiliency Testing
- GitHub Actions integration
- Backward compatibility checks
- AsyncAPI contracts for Kafka integration
- Consumer-driven contract testing
- Kafka for distributed buffering
- Persistent metrics storage
- WebSocket/SSE support
- ML-based anomaly detection