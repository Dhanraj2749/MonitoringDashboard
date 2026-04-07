from fastapi import APIRouter, Request, HTTPException
from app.core.models import ThresholdConfig

router = APIRouter()


@router.get("/metrics/latest")
async def get_latest_metrics(request: Request):
    """Get the most recent metrics snapshot"""
    snapshot = request.app.state.collector.get_latest()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No metrics available yet")
    return snapshot


@router.get("/metrics/history")
async def get_metrics_history(request: Request, limit: int = 60):
    """Get historical metrics (default last 60 seconds)"""
    history = request.app.state.collector.get_history(limit=min(limit, 100))
    return {"count": len(history), "metrics": history}


@router.get("/alerts")
async def get_alerts(request: Request, active_only: bool = False):
    """Get all alerts or only active ones"""
    alerts = request.app.state.alert_engine.get_alerts(active_only=active_only)
    return {"count": len(alerts), "alerts": alerts}


@router.get("/stats")
async def get_dashboard_stats(request: Request):
    """Get combined dashboard statistics"""
    collector_stats = request.app.state.collector.get_stats()
    alert_stats = request.app.state.alert_engine.get_stats()
    return {**collector_stats, **alert_stats}


@router.get("/health")
async def health_check(request: Request):
    """Service health check"""
    snapshot = request.app.state.collector.get_latest()
    return {
        "status": "healthy",
        "service": "MonitoringDashboard",
        "has_metrics": snapshot is not None,
        "active_alerts": request.app.state.alert_engine.get_stats()["active_alerts"]
    }


@router.put("/thresholds")
async def update_thresholds(request: Request, config: ThresholdConfig):
    """Update alert thresholds dynamically"""
    request.app.state.alert_engine.update_thresholds(config)
    return {"message": "Thresholds updated", "config": config}
