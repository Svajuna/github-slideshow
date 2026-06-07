from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AGENT_", extra="ignore")

    github_webhook_secret: str = ""

    slack_signing_secret: str = ""
    slack_bot_token: str = ""
    slack_default_channel: str = "#alerts"

    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = ""
    jira_webhook_token: str = ""

    linear_api_key: str = ""
    linear_team_id: str = ""
    linear_webhook_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
