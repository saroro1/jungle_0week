from dataclasses import dataclass


@dataclass()
class RankingDto:
    id: str
    type: str
    score: int
