from typing import Set
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Websocket Connected ({len(self.active_connections)}) clients")

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.discard(websocket)
            logger.info(f"Websocket Disconnected ({len(self.active_connections)}) clients")

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WS Message: {e}")
                await self.disconnect(connection)

ws_manager = WebSocketManager()