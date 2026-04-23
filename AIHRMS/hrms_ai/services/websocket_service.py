from ..websocket.websocket import ws_manager
import logging

logger = logging.getLogger(__name__)


class WebSocketNotifier:
    @staticmethod
    async def send_project_notification(
        project_name: str,
        message: str
    ):
        await ws_manager.broadcast({
            "type": "PROJECT_DEADLINE",
            "project": project_name,
            "message": message
        })

    @staticmethod
    async def send_notification(
        message_type: str,
        message: str
    ):
        await ws_manager.broadcast({
            "type": message_type,
            "message": message
        })

    async def new_notification_notifier(self):
        await ws_manager.broadcast({
            "notification": True
        })