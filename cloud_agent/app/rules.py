from dataclasses import dataclass
from typing import Callable

from .schemas import ActionSpec, NormalizedEvent

Predicate = Callable[[NormalizedEvent], bool]


@dataclass(frozen=True)
class Rule:
    name: str
    when: Predicate
    actions: tuple[ActionSpec, ...]


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def default_rules(default_channel: str) -> list[Rule]:
    return [
        Rule(
            name="github-pr-opened-notify-slack-and-create-jira",
            when=lambda event: event.source == "github"
            and event.event_type == "pull_request"
            and event.action == "opened",
            actions=(
                ActionSpec(
                    kind="slack_message",
                    params={
                        "channel": default_channel,
                        "text": (
                            "New PR opened by {actor}: *{title}* ({url}) "
                            "[event={event_type}:{action}]"
                        ),
                    },
                ),
                ActionSpec(
                    kind="jira_issue",
                    params={
                        "summary": "Review PR: {title}",
                        "description": "Please review pull request: {url}",
                        "issue_type": "Task",
                    },
                ),
            ),
        ),
        Rule(
            name="jira-issue-updated-notify-slack",
            when=lambda event: event.source == "jira" and event.event_type == "jira:issue_updated",
            actions=(
                ActionSpec(
                    kind="slack_message",
                    params={
                        "channel": default_channel,
                        "text": "Jira issue updated by {actor}: *{title}* ({url})",
                    },
                ),
            ),
        ),
        Rule(
            name="slack-app-mention-create-linear",
            when=lambda event: event.source == "slack"
            and event.event_type in {"event_callback", "app_mention"},
            actions=(
                ActionSpec(
                    kind="linear_issue",
                    params={
                        "title": "Follow-up from Slack mention by {actor}",
                        "description": "{title}",
                    },
                ),
            ),
        ),
    ]


def select_actions(event: NormalizedEvent, rules: list[Rule]) -> list[ActionSpec]:
    selected: list[ActionSpec] = []
    for rule in rules:
        if rule.when(event):
            selected.extend(rule.actions)
    return selected


def render_action_params(action: ActionSpec, event: NormalizedEvent) -> ActionSpec:
    rendered: dict[str, object] = {}
    context = _SafeFormatDict(
        source=event.source,
        event_type=event.event_type,
        action=event.action,
        title=event.title,
        actor=event.actor,
        entity_id=event.entity_id,
        url=event.url,
    )
    for key, value in action.params.items():
        if isinstance(value, str):
            rendered[key] = value.format_map(context)
        else:
            rendered[key] = value
    return ActionSpec(kind=action.kind, params=rendered)
