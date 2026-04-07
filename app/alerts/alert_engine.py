import asyncio
import logging
import uuid
from datetime import datetime
from app.core.models import Alert, AlertSeverity, ThresholdConfig, MetricSnapshot
from app.collectors.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Rule-based anomaly detection engine.
    Monitors metrics against configurable thresholds.
    Production: integrate with Azure Monitor Alerts / PagerDuty.
    """

    def __init__(self, collector: MetricsCollector):
        self._collector = collector
        self._running = False
        self._alerts: list[Alert] = []
        self._thresholds = ThresholdConfig()
        self._active_alert_keys: set[str] = set()  # Prevent duplicate alerts

    async def start(self):
        self._running = True
        logger.info("AlertEngine started — monitoring thresholds")
        while self._running:
            try:
                snapshot = self._collector.get_latest()
                if snapshot:
                    await self._evaluate(snapshot)
                await asyncio.sleep(5)  # Check every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("AlertEngine error: %s", str(e))

    def stop(self):
        self._running = False

    async def _evaluate(self, snapshot: MetricSnapshot):
        checks = [
            ("cpu", snapshot.cpu_percent, self._thresholds.cpu_warning, self._thresholds.cpu_critical, "CPU usage"),
            ("memory", snapshot.memory_percent, self._thresholds.memory_warning, self._thresholds.memory_critical, "Memory usage"),
            ("disk", snapshot.disk_percent, self._thresholds.disk_warning, self._thresholds.disk_critical, "Disk usage"),
            ("error_rate", snapshot.error_rate, self._thresholds.error_rate_warning, self._thresholds.error_rate_critical, "Error rate"),
            ("response_time", snapshot.avg_response_time_ms, self._thresholds.response_time_warning_ms, self._thresholds.response_time_critical_ms, "Response time"),
        ]

        for metric, value, warn_threshold, crit_threshold, label in checks:
            if value >= crit_threshold:
                await self._fire_alert(metric, AlertSeverity.CRITICAL, label, value, crit_threshold)
            elif value >= warn_threshold:
                await self._fire_alert(metric, AlertSeverity.WARNING, label, value, warn_threshold)
            else:
                self._resolve_alert(metric)

    async def _fire_alert(self, metric: str, severity: AlertSeverity, label: str, value: float, threshold: float):
        key = f"{metric}_{severity}"
        if key in self._active_alert_keys:
            return  # Already firing

        unit = "%" if metric != "response_time" else "ms"
        alert = Alert(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            severity=severity,
            metric=metric,
            message=f"{severity.upper()}: {label} is {value:.1f}{unit} (threshold: {threshold}{unit})",
            value=value,
            threshold=threshold
        )
        self._alerts.append(alert)
        self._active_alert_keys.add(key)
        logger.warning("[AlertEngine] %s", alert.message)

    def _resolve_alert(self, metric: str):
        for severity in [AlertSeverity.WARNING, AlertSeverity.CRITICAL]:
            key = f"{metric}_{severity}"
            if key in self._active_alert_keys:
                self._active_alert_keys.discard(key)
                # Mark latest matching alert as resolved
                for alert in reversed(self._alerts):
                    if alert.metric == metric and not alert.resolved:
                        alert.resolved = True
                        alert.resolved_at = datetime.utcnow()
                        logger.info("[AlertEngine] RESOLVED: %s alert for %s", severity, metric)
                        break

    def get_alerts(self, active_only: bool = False) -> list[Alert]:
        if active_only:
            return [a for a in self._alerts if not a.resolved]
        return self._alerts[-50:]  # Last 50 alerts

    def get_stats(self) -> dict:
        all_alerts = self._alerts
        return {
            "total_alerts": len(all_alerts),
            "active_alerts": sum(1 for a in all_alerts if not a.resolved),
            "resolved_alerts": sum(1 for a in all_alerts if a.resolved),
            "critical_count": sum(1 for a in all_alerts if a.severity == AlertSeverity.CRITICAL),
            "warning_count": sum(1 for a in all_alerts if a.severity == AlertSeverity.WARNING),
        }

    def update_thresholds(self, config: ThresholdConfig):
        self._thresholds = config
        logger.info("Thresholds updated")
