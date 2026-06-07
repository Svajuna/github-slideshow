import httpx

from .base import IntegrationClient


class SlackClient(IntegrationClient):
    def __init__(self, token: str) -> None:
        super().__init__()
        self.token = token

    async def send(self, payload: dict[str, str]) -> None:
        if not self.token:
            self.logger.warning("Slack token is not configured. Skipping action.")
            return
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {self.token}"},
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok", False):
            raise RuntimeError(f"Slack API error: {data}")
