from fastapi.responses import HTMLResponse
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.websocket import ws_router
from app.collectors.metrics_collector import MetricsCollector
from app.alerts.alert_engine import AlertEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

collector = MetricsCollector()
alert_engine = AlertEngine(collector)

@asynccontextmanager
async def lifespan(app: FastAPI):
    collector_task = asyncio.create_task(collector.start())
    alert_task = asyncio.create_task(alert_engine.start())
    logging.info("Real-Time Monitoring Dashboard started")
    logging.info("Metrics collection running — WebSocket streaming active")
    yield
    collector.stop()
    alert_engine.stop()
    collector_task.cancel()
    alert_task.cancel()

app = FastAPI(
    title="Real-Time Monitoring Dashboard",
    description="Cloud-native monitoring system with real-time WebSocket streaming, metrics collection, anomaly detection, and alerting.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(ws_router)
app.state.collector = collector
app.state.alert_engine = alert_engine
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    import os
    with open(os.path.join(os.path.dirname(__file__), "static/index.html")) as f:
        return f.read()