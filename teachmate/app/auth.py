"""Verify the teacher's Tcherly access token (same JWT_SECRET as the Node app)."""
import jwt
from fastapi import Header, HTTPException

from .config import settings


class Teacher:
    def __init__(self, teacher_id: str, email: str, authorization: str):
        self.id = teacher_id
        self.email = email
        # Forwarded unchanged to the Node API, which re-checks it and lesson ownership.
        self.authorization = authorization


def current_teacher(authorization: str = Header(...)) -> Teacher:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Expected 'Authorization: Bearer <token>'")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please refresh the page")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return Teacher(str(payload["_id"]), payload.get("email", ""), authorization)
