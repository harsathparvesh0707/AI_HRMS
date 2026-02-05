from ..websocket.websocket import ws_manager


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