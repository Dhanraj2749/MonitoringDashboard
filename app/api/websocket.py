import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected")
    try:
        collector = websocket.app.state.collector
        alert_engine = websocket.app.state.alert_engine
        while True:
            snapshot = collector.get_latest()
            alerts = alert_engine.get_alerts(active_only=True)
            if snapshot:
                data = snapshot.dict()
                data["timestamp"] = str(data["timestamp"])
                payload = {
                    "type": "metrics",
                    "data": data,
                    "active_alerts": len(alerts),
                    "alert_details": [
                        {
                            "severity": a.severity,
                            "message": a.message,
                            "metric": a.metric
                        } for a in alerts[:5]
                    ]
                }
                await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error("WebSocket error: %s", e)