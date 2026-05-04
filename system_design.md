# Mini Datadog - System Design

## 1) System Overview

Mini Datadog is a real-time log ingestion and anomaly detection backend built with FastAPI, in-memory buffering, asynchronous workers, and MongoDB storage.  
It uses a queue-based architecture to decouple API ingestion from processing/storage, improving resilience under burst traffic and keeping the ingestion path fast.

## 2) Architecture Diagram (Text-Based)

```text
Client Services
    |
    v
FastAPI Ingestion API (POST /logs) ----------------------+
    |                                                    |
    v                                                    |
In-Memory Queue (buffer + backpressure)                 |
    |                                                    |
    v                                                    |
Background Worker(s):                                    |
  - structured parsing                                   |
  - batch processing                                     |
  - hashmap frequency tracking                           |
  - sliding window error analytics                       |
  - anomaly detection                                    |
    |                                                    |
    +---------------------------> MongoDB (log storage)  |
                                                         |
FastAPI Metrics API (GET /metrics) <---------------------+
  - throughput
  - error analytics
  - service insights
  - anomaly snapshot
```

## 3) Data Flow

- Client sends log to `POST /logs`.
- API validates payload (Pydantic), auto-adds timestamp if missing, and enqueues event.
- Queue buffers bursts and enforces backpressure (`429` on overflow).
- Worker consumes logs in batches, performs normalization, dedupe checks, and processing.
- Processing engine updates hashmap counters and sliding windows (current 5 min vs previous 5 min).
- Anomaly detector compares windowed errors (`current > 2x previous`) with cooldown to avoid noisy repeats.
- Worker persists processed logs to MongoDB using batch inserts.
- `GET /metrics` returns pre-aggregated in-memory observability snapshot (no DB reads on request path).

## 4) Scaling Strategy

- Add a load balancer in front of FastAPI API instances.
- Replace in-memory queue with Kafka (or similar durable broker) for distributed buffering.
- Scale workers horizontally across multiple instances/containers.
- Partition logs by `service` to improve parallelism and reduce hot partitions.
- Use MongoDB sharding to scale write throughput and storage across nodes.

## 5) Trade-offs

- **Consistency vs Availability:** Eventual consistency due to asynchronous queue + worker processing.
- **Latency vs Accuracy:** Small processing delay from batching/queueing improves throughput and stability.
- **Simplicity vs Scalability:** In-memory queue is simple and fast, but not distributed or durable across nodes.

## 6) Bottlenecks & Improvements

- **Queue capacity limits:** bounded memory may reject traffic under sustained spikes.  
  **Fix:** move to Kafka with retention and replay.
- **Single-node worker limits:** one node can become CPU-bound during heavy parsing/analytics.  
  **Fix:** distributed worker pool with partition-aware consumption.
- **DB write throughput:** Mongo write saturation at very high ingest rates.  
  **Fix:** larger batch writes, sharding, and write-optimized cluster sizing.

## 7) Why This Design Works

- Decouples ingestion from processing, keeping API latency low under load.
- Uses efficient in-memory structures (hashmap + deque windows) for near-constant-time analytics.
- Detects anomalies in near real-time using rolling error-window comparisons.
- Evolves cleanly from single-node simplicity to distributed, high-throughput architecture.
