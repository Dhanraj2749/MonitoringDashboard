import asyncio
import random
import logging
from datetime import datetime
from collections import deque
from app.core.models import MetricSnapshot

logger = logging.getLogger(__name__)

MAX_HISTORY = 100  # Keep last 100 snapshots


class MetricsCollector:
    """
    Collects system metrics every second.
    Simulates realistic CPU, memory, network, and request metrics.
    Production: replace with psutil for real system metrics,
    or Azure Monitor SDK for cloud metrics.
    """

    def __init__(self):
        self._running = False
        self._history: deque[MetricSnapshot] = deque(maxlen=MAX_HISTORY)
        self._metrics_count = 0
        self._start_time = datetime.utcnow()
        self._subscribers: list = []

        # Simulated state for realistic patterns
        self._base_cpu = 30.0
        self._base_memory = 45.0
        self._base_rps = 150.0
        self._spike_counter = 0

    async def start(self):
        self._running = True
        logger.info("MetricsCollector started — collecting every 1s")
        while self._running:
            try:
                snapshot = self._collect()
                self._history.append(snapshot)
                self._metrics_count += 1

                # Notify all WebSocket subscribers
                for subscriber in self._subscribers[:]:
                    try:
                        await subscriber(snapshot)
                    except Exception:
                        self._subscribers.remove(subscriber)

                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Collector error: %s", str(e))

    def stop(self):
        self._running = False

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def unsubscribe(self, callback):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _collect(self) -> MetricSnapshot:
        """Simulate realistic metrics with occasional spikes"""
        self._spike_counter += 1

        # Simulate CPU spikes every 30 seconds
        cpu_spike = 40.0 if self._spike_counter % 30 == 0 else 0.0
        cpu = min(100.0, self._base_cpu + cpu_spike + random.uniform(-5, 10))

        # Memory slowly grows then GC kicks in
        memory_drift = (self._spike_counter % 60) * 0.3
        memory = min(95.0, self._base_memory + memory_drift + random.uniform(-2, 2))

        # RPS fluctuates realistically
        rps = max(0, self._base_rps + random.uniform(-30, 50))

        # Error rate spikes occasionally
        error_rate = random.uniform(0, 2)
        if self._spike_counter % 45 == 0:
            error_rate = random.uniform(8, 15)  # Simulate error spike

        return MetricSnapshot(
            timestamp=datetime.utcnow(),
            cpu_percent=round(cpu, 2),
            memory_percent=round(memory, 2),
            memory_used_mb=round(memory * 81.92, 2),  # 8GB total
            disk_percent=round(random.uniform(55, 65), 2),
            network_bytes_sent=round(random.uniform(1000, 50000), 2),
            network_bytes_recv=round(random.uniform(5000, 100000), 2),
            active_connections=int(random.uniform(50, 300)),
            requests_per_second=round(rps, 2),
            error_rate=round(error_rate, 2),
            avg_response_time_ms=round(random.uniform(50, 300) + (cpu_spike * 5), 2)
        )

    def get_latest(self) -> MetricSnapshot | None:
        return self._history[-1] if self._history else None

    def get_history(self, limit: int = 60) -> list[MetricSnapshot]:
        return list(self._history)[-limit:]

    def get_stats(self) -> dict:
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        return {
            "metrics_collected": self._metrics_count,
            "uptime_seconds": round(uptime, 2),
            "active_subscribers": len(self._subscribers),
            "history_size": len(self._history)
        }
