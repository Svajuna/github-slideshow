import httpx

from .base import IntegrationClient


class JiraClient(IntegrationClient):
    def __init__(self, base_url: str, email: str, api_token: str, project_key: str) -> None:
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.project_key = project_key

    async def send(self, payload: dict[str, str]) -> None:
        if not all([self.base_url, self.email, self.api_token, self.project_key]):
            self.logger.warning("Jira settings incomplete. Skipping action.")
            return

        issue_type = payload.get("issue_type", "Task")
        body = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": payload["summary"],
                "description": payload.get("description", ""),
                "issuetype": {"name": issue_type},
            }
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/rest/api/3/issue",
                auth=(self.email, self.api_token),
                json=body,
                headers={"Accept": "application/json"},
            )
        response.raise_for_status()
