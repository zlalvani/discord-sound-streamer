from typing import Dict, Literal, Optional

from httpx import AsyncClient
from pydantic import BaseModel

from discord_sound_streamer.clients.invidious.schemas.video import VideoModel
from discord_sound_streamer.config import CONFIG


async def get_video(id: str) -> VideoModel:
    url = f"/api/v1/videos/{id}?fields=" + ",".join(VideoModel.get_fields())
    return VideoModel.parse_raw(await _request("GET", url))


async def _request(
    method: Literal["GET", "PUT", "PATCH", "POST"],
    url: str,
    payload: Optional[BaseModel] = None,
    headers: Optional[Dict[str, str]] = None,
) -> str:
    url = url = f"{CONFIG.INVIDIOUS_URL}" + (url if url.startswith("/") else f"/{url}")

    async with AsyncClient() as client:
        response = await client.request(
            method,
            url,
            headers=headers,
            content=payload.json(exclude_unset=True) if payload else None,
        )
        response.raise_for_status()
        return response.text
