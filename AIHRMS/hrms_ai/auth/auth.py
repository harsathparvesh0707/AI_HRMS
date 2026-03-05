from jose import JWTError, jwt
from datetime import datetime, timedelta
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)

class Token:
    def __init__(self):
        self.SECRET_KEY = settings.secret_key
        self.ALGORITHM = settings.algorithm
        self.ACCESS_TOEKN_EXPIRE_HOURS = settings.expire_time

    def _create_access_token(self, user_id: int, username: str):
        try:
            expire_time = datetime.utcnow() + timedelta(days=self.ACCESS_TOEKN_EXPIRE_HOURS)
            payload = {"id": user_id, "username": username, "exp": expire_time}
            access_token = jwt.encode(payload, self.SECRET_KEY, self.ALGORITHM)
            return access_token
        except Exception as e:
            logger.error(e)
            raise

    def _decode_access_token(self, token: str):
        try:
            payload = jwt.decode(
                token,
                self.SECRET_KEY,
                algorithms=[self.ALGORITHM]
            )

            user_id = payload.get("id")
            username = payload.get("username")

            if user_id is None or username is None:
                raise 

            return {
                "user_id": user_id,
                "username": username
            }

        except JWTError:
            raise


