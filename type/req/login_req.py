from dataclasses import dataclass
from pydantic import BaseModel, ValidationError


class LoginReq(BaseModel):
    id: str
    password: str
