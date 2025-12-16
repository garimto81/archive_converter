"""WebSocket Router for Real-time Updates"""

from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

router = APIRouter()

# Connected clients
connected_clients: Set[WebSocket] = set()


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)

    async def send_progress(
        self,
        video_id: str,
        progress: float,
        speed: float,
        eta: int,
        status: str,
    ):
        """Send download progress update"""
        await self.broadcast({
            "type": "progress",
            "video_id": video_id,
            "progress": progress,
            "speed": speed,
            "eta": eta,
            "status": status,
        })

    async def send_completed(self, video_id: str, file_path: str, file_size: int):
        """Send download completed notification"""
        await self.broadcast({
            "type": "completed",
            "video_id": video_id,
            "file_path": file_path,
            "file_size": file_size,
        })

    async def send_failed(self, video_id: str, error: str):
        """Send download failed notification"""
        await self.broadcast({
            "type": "failed",
            "video_id": video_id,
            "error": error,
        })

    async def send_queue_update(self, queue_status: dict):
        """Send queue status update"""
        await self.broadcast({
            "type": "queue_update",
            **queue_status,
        })


# Global connection manager
manager = ConnectionManager()


def get_ws_manager() -> ConnectionManager:
    """Get WebSocket manager instance"""
    return manager


@router.websocket("/downloads")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for download progress"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()

            # Handle client messages
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
