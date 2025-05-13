from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel


class ModifyUserReq(BaseModel):
    id: Optional[str]
    password: Optional[str]
    nickname: Optional[str]
