from pathlib import Path
import jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

path = Path(__file__).parent.parent / ".env"
load_dotenv(path)


def create_token(user_id: str) -> str:
    secret = os.getenv("SECRET_KEY")
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str) -> str:
    if is_valid_token(token):
        secret = os.getenv("SECRET_KEY")
        jwt_decoded = jwt.decode(
            token, secret, algorithms=["HS256"], options={"require": ["exp", "sub"]}
        )
        return str(jwt_decoded.get("sub"))


def is_valid_token(token: str) -> bool:
    try:
        jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
        return True
    except jwt.InvalidTokenError:
        return False
