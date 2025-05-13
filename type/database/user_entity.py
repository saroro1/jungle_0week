from dataclasses import dataclass, field
from datetime import datetime
from typing import TypedDict, Optional, List, Dict, Any

from bson import ObjectId
import bcrypt

from constant import DBContainer, word_type
from pymongo.collection import Collection
from pymongo.results import UpdateResult


class HighScoreDict(TypedDict):
    kr: int
    en: int
    complex : int


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
        collection: Collection = DBContainer.user_db
        user_data = collection.find_one({"id": user_id})
        if user_data:
            return cls.from_dict(user_data)
        else:
            return None

    @classmethod
    def getMyRanking(cls, user_id: str) -> Optional[HighScoreDict]:
        collection: Collection = DBContainer.user_db
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
                complex_rank = collection.count_documents(
                    {"high_score.complex": {"$gt": high_score.get('complex', 0)}}
                ) + 1

                return HighScoreDict(kr=kr_rank, en=en_rank, complex=complex_rank)

            except Exception as e:
                print(f"Error calculating ranking for user {user_id}: {e}")
                return None
        else:
            return None

    @classmethod
    def getLeaderBoard(cls, type: str, page: int, count: int) -> List['UserEntity']:
        if type not in word_type:
            raise ValueError("Invalid type. Must be 'kr' or 'en'.")
        collection: Collection = DBContainer.user_db

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

    @classmethod
    def setHighScore(cls, user_id: str, score_type: str, score: int) -> Optional[UpdateResult]:
        if score_type not in word_type:
            raise ValueError("Invalid score_type. Must be 'kr' or 'en'.")

        collection: Collection = DBContainer.user_db
        update_field = f"high_score.{score_type}"

        try:
            user_data = collection.find_one({"id": user_id}, {update_field: 1})

            if user_data and 'high_score' in user_data and score_type in user_data.get('high_score', {}):
                current_score = user_data['high_score'][score_type]
                if score > current_score:
                    result = collection.update_one(
                        {"id": user_id},
                        {"$set": {update_field: score}}
                    )
                    return result
                else:
                    return None
            elif user_data:
                result = collection.update_one(
                    {"id": user_id},
                    {"$set": {update_field: score}}
                )
                return result
            else:
                return None

        except Exception as e:
            print(f"Error setting high score for user {user_id} ({score_type}): {e}")
            return None

    @classmethod
    def updateUser(cls, user_id: str, new_nickname: Optional[str] = None, new_password: Optional[str] = None) -> \
            Optional[UpdateResult]:
        collection: Collection = DBContainer.user_db
        update_fields: Dict[str, Any] = {}

        if new_nickname is not None and new_nickname.strip() != "":
            if len(new_nickname) > 20:
                raise ValueError("닉네임은 20자를 넘을 수 없어요")
            update_fields["nickname"] = new_nickname.strip()

        if new_password is not None and new_password != "":
            try:
                hashed_password_bytes = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
                update_fields["password"] = hashed_password_bytes.decode("UTF-8")
            except Exception as e:
                print(f"Error hashing new password for user {user_id}: {e}")
                return None

        if not update_fields:
            return None

        try:
            result = collection.update_one(
                {"id": user_id},
                {"$set": update_fields}
            )
            return result
        except Exception as e:
            print(f"Error updating user {user_id}: {e}")
            return None
