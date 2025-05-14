from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel


class ModifyUserReq(BaseModel):
    id: str
    password: Optional[str]
    nickname: Optional[str]
