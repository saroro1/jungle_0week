from dataclasses import dataclass

from pydantic import BaseModel


class SignUpReq(BaseModel):
    id: str
    password: str
    nickname: str
