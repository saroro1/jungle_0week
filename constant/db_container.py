from dataclasses import dataclass
from pymongo.collection import Collection


class DBContainer:
    user_db: Collection
    ranking_db: Collection
