import os
from datetime import datetime, timedelta
from typing import Dict, TypedDict

from dotenv import load_dotenv

from jwt import ExpiredSignatureError, InvalidTokenError, encode, decode

load_dotenv()


class IUserJwt(TypedDict):
    id: str


class Jwt:
    @staticmethod
    def encode(user_id: str):
        return (
            encode({
                "id": user_id,
                "exp": datetime.now() + timedelta(hours=1)
            },
                os.environ.get('JWT_SECRET'),
                algorithm="HS256"
            )
        )

    @staticmethod
    def decode(text: str) -> IUserJwt:
        return decode(
                text,
                os.environ.get('JWT_SECRET'),
                algorithms="HS256"
            )

    @staticmethod
    def is_valid(text: str) -> bool:
        try:
            decode(
                text,
                os.environ.get('JWT_SECRET'),
                algorithms="HS256"
            )
            return True
        except (ExpiredSignatureError, InvalidTokenError):
            return False
