import bcrypt
from ..core.database import get_db_session
from sqlalchemy import text
import logging
from fastapi.exceptions import HTTPException
from .auth import Token

logger = logging.getLogger(__name__)


class Authentication:
    def __init__(self):
        self.token = Token()

    @staticmethod
    def _hash_password(password: str) -> str:
        if not password:
            raise HTTPException(status_code=400, detail="Password is required")
        # bcrypt requires bytes
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

        return hashed.decode("utf-8")

    @staticmethod
    def _verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    
    async def _check_existing_user(self, username: str):
        with get_db_session() as session:
            try:
                result = session.execute(text("SELECT id, username, password FROM users WHERE username = :username"), {"username": username}).fetchone()
                return result
            except Exception as e:
                logger.error(e)
                raise
        
    async def _create_user(self, user: dict):
        with get_db_session() as session:
            try:
                session.execute(text("INSERT INTO users (username, password) VALUES (:username, :password)"), {"username": user.get("username"), "password":user.get("password")})
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(e)
                raise
    
    async def _create_registered_user(self, user: dict):
        try:
            existing_user = await self._check_existing_user(user.get("username"))
            if existing_user:
                logger.info("Username Already Exists...")
                raise HTTPException(status_code=400, detail="Username already exists")
            
            hashed_password = self._hash_password(user.get("password"))
            user["password"] = hashed_password
            await self._create_user(user)
            logger.info("User Created Succesfully...")
            return {"message": "User Registered Successfully"}
        except Exception as e:
            logger.error(e)
            raise

    async def _user_login(self, user: dict):
        try:
            user_details = await self._check_existing_user(user.get("username"))
            if not user_details:
                logger.error("No Account found for this username")
                raise HTTPException(status_code=400, detail="No Account found for this username")
            user_id, username, password = user_details
            if not self._verify_password(user.get("password"), password):
                raise HTTPException(status_code=401, detail="Invalid Credentials")
            access_token = self.token._create_access_token(user_id, username)
            logger.info("Token Created Succesfully")
            return {"access_token": access_token, "token_type": "Bearer"}
        except Exception as e:
            logger.error(e)
            raise