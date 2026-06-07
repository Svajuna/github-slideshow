from typing import Any, Literal

from pydantic import BaseModel, Field


class NormalizedEvent(BaseModel):
    source: Literal["github", "slack", "jira", "linear", "unknown"]
    event_type: str
    action: str = "unknown"
    title: str = ""
    actor: str = ""
    entity_id: str = ""
    url: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


class ActionSpec(BaseModel):
    kind: Literal["slack_message", "jira_issue", "linear_issue"]
    params: dict[str, Any] = Field(default_factory=dict)


class WebhookResponse(BaseModel):
    status: Literal["accepted", "ignored"]
    source: str
    event_type: str
    actions_count: int
