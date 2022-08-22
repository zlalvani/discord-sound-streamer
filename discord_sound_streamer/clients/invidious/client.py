from typing import Dict, Literal, Optional

from httpx import AsyncClient, Timeout, TransportError
from pydantic import BaseModel
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential

from discord_sound_streamer.clients.invidious.schemas.video import VideoModel
from discord_sound_streamer.config import CONFIG


async def get_video(id: str) -> VideoModel:
    url = f"/api/v1/videos/{id}?fields=" + ",".join(VideoModel.get_fields())
    return VideoModel.parse_raw(await _request("GET", url))


@retry(
    retry=retry_if_exception_type(TransportError),
    wait=wait_exponential(multiplier=2, exp_base=2),
    stop=stop_after_attempt(3),
)
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
            timeout=Timeout(connect=5, read=10),
        )
        response.raise_for_status()
        return response.text
