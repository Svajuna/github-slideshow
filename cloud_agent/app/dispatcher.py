import logging

from .integrations.jira import JiraClient
from .integrations.linear import LinearClient
from .integrations.slack import SlackClient
from .rules import Rule, render_action_params, select_actions
from .schemas import ActionSpec, NormalizedEvent


class Dispatcher:
    def __init__(
        self,
        slack_client: SlackClient,
        jira_client: JiraClient,
        linear_client: LinearClient,
        rules: list[Rule],
    ) -> None:
        self.slack_client = slack_client
        self.jira_client = jira_client
        self.linear_client = linear_client
        self.rules = rules
        self.logger = logging.getLogger(self.__class__.__name__)

    def plan_actions(self, event: NormalizedEvent) -> list[ActionSpec]:
        return [render_action_params(action, event) for action in select_actions(event, self.rules)]

    async def execute(self, actions: list[ActionSpec]) -> None:
        for action in actions:
            try:
                await self._execute_action(action)
            except Exception:
                self.logger.exception("Failed executing action: %s", action.model_dump())

    async def _execute_action(self, action: ActionSpec) -> None:
        if action.kind == "slack_message":
            await self.slack_client.send(action.params)
            return
        if action.kind == "jira_issue":
            await self.jira_client.send(action.params)
            return
        if action.kind == "linear_issue":
            await self.linear_client.send(action.params)
            return
        raise ValueError(f"Unsupported action type: {action.kind}")
