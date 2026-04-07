from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class AlertSeverity(str, Enum):
    INFO    = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MetricSnapshot(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_percent: float
    network_bytes_sent: float
    network_bytes_recv: float
    active_connections: int
    requests_per_second: float
    error_rate: float
    avg_response_time_ms: float


class Alert(BaseModel):
    id: str
    timestamp: datetime
    severity: AlertSeverity
    metric: str
    message: str
    value: float
    threshold: float
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class ThresholdConfig(BaseModel):
    cpu_warning: float = 70.0
    cpu_critical: float = 90.0
    memory_warning: float = 75.0
    memory_critical: float = 90.0
    disk_warning: float = 80.0
    disk_critical: float = 95.0
    error_rate_warning: float = 5.0
    error_rate_critical: float = 10.0
    response_time_warning_ms: float = 500.0
    response_time_critical_ms: float = 1000.0


class DashboardStats(BaseModel):
    total_alerts: int
    active_alerts: int
    resolved_alerts: int
    critical_count: int
    warning_count: int
    uptime_seconds: float
    metrics_collected: int
