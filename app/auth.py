from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, HTTPException
from passlib.context import CryptContext
from app.database import SessionLocal
from app.models import User
import os

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-almashtiring-buni")
serializer = URLSafeTimedSerializer(SECRET_KEY)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return plain == hashed


def create_session(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})


def get_current_user(request: Request):
    token = request.cookies.get("session")
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=60 * 60 * 24 * 7)
    except (BadSignature, SignatureExpired):
        return None
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == data["user_id"]).first()
    finally:
        db.close()
    return user


def require_user(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=307, headers={"Location": "/login"})
    return user
