from typing import List

from pydantic import BaseModel


class VideoModel(BaseModel):
    videoId: str
    isFamilyFriendly: bool

    @classmethod
    def get_fields(cls) -> List[str]:
        return list(cls.__dict__["__fields__"].keys())
