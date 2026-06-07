from typing import Any

from .schemas import NormalizedEvent


def parse_event(source: str, payload: dict[str, Any], headers: dict[str, str]) -> NormalizedEvent:
    if source == "github":
        return _parse_github(payload, headers)
    if source == "slack":
        return _parse_slack(payload)
    if source == "jira":
        return _parse_jira(payload)
    if source == "linear":
        return _parse_linear(payload)
    return NormalizedEvent(source="unknown", event_type="unknown", payload=payload)


def _parse_github(payload: dict[str, Any], headers: dict[str, str]) -> NormalizedEvent:
    event_type = headers.get("x-github-event", "unknown")
    action = payload.get("action", "unknown")
    sender = payload.get("sender", {}) or {}
    pull_request = payload.get("pull_request", {}) or {}
    issue = payload.get("issue", {}) or {}
    repository = payload.get("repository", {}) or {}

    title = pull_request.get("title") or issue.get("title") or repository.get("full_name", "")
    entity_id = str(pull_request.get("id") or issue.get("id") or payload.get("id") or "")
    url = pull_request.get("html_url") or issue.get("html_url") or repository.get("html_url", "")

    return NormalizedEvent(
        source="github",
        event_type=event_type,
        action=action,
        title=title,
        actor=sender.get("login", ""),
        entity_id=entity_id,
        url=url,
        payload=payload,
    )


def _parse_slack(payload: dict[str, Any]) -> NormalizedEvent:
    event = payload.get("event", {}) or {}
    event_type = payload.get("type") or event.get("type") or "unknown"
    action = event.get("subtype", "event")
    actor = event.get("user", "")
    title = event.get("text", "")
    entity_id = event.get("client_msg_id", "")

    return NormalizedEvent(
        source="slack",
        event_type=event_type,
        action=action,
        title=title,
        actor=actor,
        entity_id=entity_id,
        payload=payload,
    )


def _parse_jira(payload: dict[str, Any]) -> NormalizedEvent:
    issue = payload.get("issue", {}) or {}
    fields = issue.get("fields", {}) or {}
    user = payload.get("user", {}) or {}

    return NormalizedEvent(
        source="jira",
        event_type=payload.get("webhookEvent", "unknown"),
        action=payload.get("issue_event_type_name", "unknown"),
        title=fields.get("summary", ""),
        actor=user.get("displayName", ""),
        entity_id=issue.get("id", ""),
        url=issue.get("self", ""),
        payload=payload,
    )


def _parse_linear(payload: dict[str, Any]) -> NormalizedEvent:
    data = payload.get("data", {}) or {}
    actor = payload.get("actor", {}) or {}
    event_type = payload.get("type", "unknown")
    action = payload.get("action", "unknown")

    return NormalizedEvent(
        source="linear",
        event_type=event_type,
        action=action,
        title=data.get("title", ""),
        actor=actor.get("name", ""),
        entity_id=data.get("id", ""),
        url=data.get("url", ""),
        payload=payload,
    )
