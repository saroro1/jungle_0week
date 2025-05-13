from dataclasses import dataclass, field
from datetime import datetime
from typing import TypedDict, Optional, List

from bson import ObjectId

from constant import DBContainer


class HighScoreDict(TypedDict):
    kr: int
    en: int


@dataclass
class UserEntity:
    id: str
    nickname: str
    password: str
    created_at: datetime
    high_score: HighScoreDict
    _id: ObjectId = field(default_factory=ObjectId)
    ranking: Optional[int] = None

    def to_dict(self) -> dict:
        data = {
            "_id": str(self._id),
            "id": self.id,
            "nickname": self.nickname,
            "password": self.password,
            "created_at": self.created_at.isoformat(),
            "high_score": self.high_score,
        }
        if self.ranking is not None:
            data["ranking"] = self.ranking
        return data

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            _id=data["_id"],
            id=data["id"],
            nickname=data["nickname"],
            password=data["password"],
            created_at=data["created_at"],
            high_score=data["high_score"],
            ranking=data.get("ranking"),
        )

    @classmethod
    def findUserById(cls, user_id: str):
        collection = DBContainer.user_db
        user_data = collection.find_one({"id": user_id})
        if user_data:
            return cls.from_dict(user_data)
        else:
            return None

    @classmethod
    def getMyRanking(cls, user_id: str) -> Optional[HighScoreDict]:
        collection = DBContainer.user_db
        user_data = collection.find_one({"id": user_id}, {"high_score": 1})

        if user_data and 'high_score' in user_data:
            high_score = user_data['high_score']
            try:
                kr_rank = collection.count_documents(
                    {"high_score.kr": {"$gt": high_score.get('kr', 0)}}
                ) + 1
                en_rank = collection.count_documents(
                    {"high_score.en": {"$gt": high_score.get('en', 0)}}
                ) + 1

                return HighScoreDict(kr=kr_rank, en=en_rank)

            except Exception as e:
                print(f"Error calculating ranking for user {user_id}: {e}")
                return None
        else:
            return None

    @classmethod
    def getLeaderBoard(cls, type: str, page: int, count: int) -> List['UserEntity']:
        if type not in ['kr', 'en']:
            raise ValueError("Invalid type. Must be 'kr' or 'en'.")
        collection = DBContainer.user_db

        skip = (page - 1) * count
        limit = count

        pipeline = [
            {
                "$project": {
                    "_id": 1,
                    "id": 1,
                    "nickname": 1,
                    "high_score": 1,
                    "created_at": 1,
                    "score": f"$high_score.{type}"
                }
            },
            {"$sort": {"score": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]

        leaderboard_data = collection.aggregate(pipeline)

        leaderboard = [cls.from_dict(user) for user in leaderboard_data]

        for index, user in enumerate(leaderboard):
            user.ranking = skip + index + 1

        return leaderboard
