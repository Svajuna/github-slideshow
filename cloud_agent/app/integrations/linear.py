import httpx

from .base import IntegrationClient


class LinearClient(IntegrationClient):
    def __init__(self, api_key: str, team_id: str) -> None:
        super().__init__()
        self.api_key = api_key
        self.team_id = team_id

    async def send(self, payload: dict[str, str]) -> None:
        if not self.api_key or not self.team_id:
            self.logger.warning("Linear settings incomplete. Skipping action.")
            return

        mutation = """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
          }
        }
        """
        variables = {
            "input": {
                "teamId": self.team_id,
                "title": payload["title"],
                "description": payload.get("description", ""),
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.linear.app/graphql",
                json={"query": mutation, "variables": variables},
                headers={"Authorization": self.api_key},
            )
        response.raise_for_status()
