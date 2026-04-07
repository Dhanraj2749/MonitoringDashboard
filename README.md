# Real-Time Monitoring Dashboard

A cloud-native real-time system monitoring dashboard built with **Python and FastAPI** — live metrics streaming via WebSockets, anomaly detection alerts, and a real-time browser dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           Browser Dashboard (WebSocket client)       │
│   Live charts, alerts, service health — updates/sec  │
└──────────────────────┬──────────────────────────────┘
                       │ WebSocket ws://localhost:8000/ws/metrics
                       ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend                         │
│   REST API  + WebSocket server                       │
└──────┬───────────────────────────────┬──────────────┘
       │                               │
       ▼                               ▼
┌──────────────────┐      ┌────────────────────────────┐
│ MetricsCollector │      │       AlertEngine           │
│ Collects every 1s│      │ Checks thresholds every 5s  │
│ CPU, Memory, RPS │      │ Fires WARNING / CRITICAL     │
│ Error rate, etc  │      │ Auto-resolves when normal    │
└──────────────────┘      └────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI, Pydantic |
| Real-time | WebSockets (native FastAPI) |
| Metrics | Async collector (psutil-ready) |
| Alerts | Rule-based anomaly detection engine |
| Dashboard | Vanilla JS, Canvas charts |
| Testing | pytest, pytest-asyncio |
| CI/CD | GitHub Actions |
| Container | Docker |

## Getting Started

### Run locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open dashboard: **http://localhost:8000**
Open API docs: **http://localhost:8000/docs**

### Run with Docker
```bash
docker build -t monitoring-dashboard .
docker run -p 8000:8000 monitoring-dashboard
```

### Run tests
```bash
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Live dashboard UI |
| GET | `/api/metrics/latest` | Latest metric snapshot |
| GET | `/api/metrics/history?seconds=60` | Historical metrics |
| GET | `/api/metrics/averages` | Averaged metrics |
| GET | `/api/alerts` | All alerts |
| GET | `/api/alerts/stats` | Alert statistics |
| GET | `/api/services/health` | Service health status |
| GET | `/api/dashboard/stats` | Combined stats |
| WS  | `/ws/metrics` | Live WebSocket stream |

## Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU | 70% | 90% |
| Memory | 75% | 90% |
| Error Rate | 5% | 15% |
| Response Time | 300ms | 1000ms |

## Key Features

- **Real-time WebSocket streaming** — metrics pushed to all connected clients every second
- **Auto-reconnecting dashboard** — browser reconnects automatically on disconnect
- **Anomaly detection** — rule-based alert engine fires and auto-resolves alerts
- **Service health panel** — monitors multiple services with uptime and response times
- **Live charts** — Canvas-based CPU and memory charts with 60-second history
- **Multi-client support** — all connected browsers receive the same live stream
- **Docker ready** — containerized for Azure Container Apps deployment
- **GitHub Actions CI** — automated test and Docker build on every push

## Production Swap Guide

| Current (Local) | Production |
|----------------|-----------|
| Simulated metrics | psutil for real CPU/memory |
| In-memory history | Redis time-series |
| Rule-based alerts | Azure Monitor / Grafana alerting |
| Single instance WS | Redis pub/sub for multi-instance |
| Local Docker | Azure Container Apps |
