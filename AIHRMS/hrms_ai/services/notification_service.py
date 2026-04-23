from datetime import datetime
from ..core.database import get_db_session
from sqlalchemy import text
from fastapi.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)




class NotificationDBService:
    async def add_new_notification(self, title: str, message: str):
        with get_db_session() as session:
            try:
                session.execute(text(
                    """
                    INSERT INTO notifications(title, message, created_at)
                    VALUES(:title, :message, :created_at)
                    """), {"title": title, "message": message, "created_at": datetime.now()}
                )
                session.commit()
                logger.info("Notification Inserted")
            except Exception as e:
                logger.error(f"Error adding notification: {e}")
                raise
    
    async def get_notifications(self, notification_id = None):
        with get_db_session() as session:
            try:
                query = "SELECT * FROM notifications"
                params = {}
                if notification_id is not None:
                    query += " WHERE id = :id"
                    params["id"] = notification_id
                query += " ORDER BY created_at DESC"
                result = session.execute(text(query), params).mappings().all()
                if not result:
                    return {"status": 200, "message": "No Notifications Found"}
                return [dict(row) for row in result]
            except Exception as e:
                logger.error(f"Error fetching notifications: {e}")
                raise

    async def mark_notification_as_read(self, notification_ids = None):
        with get_db_session() as session:
            try:
                if notification_ids is not None:
                    query = "UPDATE notifications SET is_read = TRUE WHERE id = ANY(:ids)"
                    params = {"ids": notification_ids}
                else:
                    query = "UPDATE notifications SET is_read = TRUE WHERE is_read = FALSE"
                    params = {}
                result = session.execute(text(query), params)
                session.commit()
                if notification_ids and result.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Notification not found")
                logger.info("Notification Marked as Read")
                return {"status": 200, "message": "Notification marked as read"}
            except Exception as e:
                logger.error(f"Error marking notification as read: {e}")
                raise HTTPException(status_code=404, detail=str(e))
            
    async def mark_as_unread(self, notification_ids):
        with get_db_session() as session:
            try:
                query = "UPDATE notifications SET is_read = FALSE WHERE id = ANY(:ids)"
                params = {"ids": notification_ids}
                result = session.execute(text(query), params)
                session.commit()
                if notification_ids and result.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Notification not found")
                logger.info(f"Notification marked as unread")
                return {"status": 200, "message": "Notification marked as unread"}
            except Exception as e:
                logger.error(f"Error marking notification as unread: {e}")
                raise HTTPException(status_code=404, detail=str(e))
                    
            
    async def delete_notification(self, notification_ids):
        with get_db_session() as session:
            try:
                query = "DELETE FROM notifications WHERE id = ANY(:ids)"
                params = {"ids": notification_ids}
                result = session.execute(text(query), params)
                session.commit()
                if notification_ids and result.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Notification not found")
                logger.info("Notification deleted")
                return {"status": 200, "message": "Notification deleted"}
            except Exception as e:
                logger.error(f"Error deleting notification: {e}")
                raise HTTPException(status_code=404, detail=str(e))
            
    async def get_unread_notification_count(self):
        with get_db_session() as session:
            try:
                result = session.execute(text("SELECT COUNT(*) as count FROM notifications WHERE is_read = FALSE")).fetchone()
                return {"status": 200, "count": result[0] if result else 0}
            except Exception as e:
                logger.error(f"Error fetching unread notification count: {e}")
                raise
