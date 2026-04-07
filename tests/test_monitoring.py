import asyncio
import pytest
from app.collectors.metrics_collector import MetricsCollector
from app.alerts.alert_engine import AlertEngine
from app.core.models import ThresholdConfig, AlertSeverity


@pytest.mark.asyncio
async def test_collector_returns_snapshot():
    collector = MetricsCollector()
    snapshot = collector._collect()
    assert snapshot is not None
    assert 0 <= snapshot.cpu_percent <= 100
    assert 0 <= snapshot.memory_percent <= 100
    assert snapshot.requests_per_second >= 0


@pytest.mark.asyncio
async def test_collector_history():
    collector = MetricsCollector()
    for _ in range(5):
        collector._history.append(collector._collect())
    history = collector.get_history(limit=3)
    assert len(history) == 3


@pytest.mark.asyncio
async def test_collector_latest():
    collector = MetricsCollector()
    assert collector.get_latest() is None
    collector._history.append(collector._collect())
    assert collector.get_latest() is not None


@pytest.mark.asyncio
async def test_alert_fires_on_critical_cpu():
    collector = MetricsCollector()
    engine = AlertEngine(collector)

    # Force a critical CPU snapshot
    snapshot = collector._collect()
    snapshot.cpu_percent = 95.0
    await engine._evaluate(snapshot)

    alerts = engine.get_alerts()
    assert len(alerts) > 0
    critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
    assert len(critical_alerts) > 0


@pytest.mark.asyncio
async def test_alert_resolves():
    collector = MetricsCollector()
    engine = AlertEngine(collector)

    # Fire alert
    snapshot = collector._collect()
    snapshot.cpu_percent = 95.0
    await engine._evaluate(snapshot)
    assert engine.get_stats()["active_alerts"] > 0

    # Resolve alert
    snapshot.cpu_percent = 30.0
    await engine._evaluate(snapshot)
    assert engine.get_stats()["active_alerts"] == 0


@pytest.mark.asyncio
async def test_threshold_update():
    collector = MetricsCollector()
    engine = AlertEngine(collector)
    new_config = ThresholdConfig(cpu_warning=50.0, cpu_critical=80.0)
    engine.update_thresholds(new_config)
    assert engine._thresholds.cpu_warning == 50.0
    assert engine._thresholds.cpu_critical == 80.0


@pytest.mark.asyncio
async def test_no_duplicate_alerts():
    collector = MetricsCollector()
    engine = AlertEngine(collector)

    snapshot = collector._collect()
    snapshot.cpu_percent = 95.0

    # Fire same alert 3 times
    await engine._evaluate(snapshot)
    await engine._evaluate(snapshot)
    await engine._evaluate(snapshot)

    cpu_alerts = [a for a in engine.get_alerts() if a.metric == "cpu"]
    assert len(cpu_alerts) == 1  # Only one alert fired
