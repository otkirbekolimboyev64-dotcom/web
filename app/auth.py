from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, HTTPException
import bcrypt
from app.database import SessionLocal
from app.models import User
import os

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-almashtiring-buni")
serializer = URLSafeTimedSerializer(SECRET_KEY)

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        pwd_bytes = plain.encode("utf-8")
        if len(pwd_bytes) > 72:
            pwd_bytes = pwd_bytes[:72]
        hash_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
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
