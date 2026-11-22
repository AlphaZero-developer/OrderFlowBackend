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
    secret = os.getenv("SECRET_KEY")
    try:
        jwt_decoded = jwt.decode(
            token, secret, algorithms=["HS256"], options={"require": ["exp", "sub"]}
        )
        return str(jwt_decoded.get("sub"))
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise
