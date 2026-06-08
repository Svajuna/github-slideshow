import pathlib
import sys
import unittest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.rules import default_rules, render_action_params, select_actions
from app.schemas import ActionSpec, NormalizedEvent


class RulesTestCase(unittest.TestCase):
    def test_selects_actions_for_opened_pull_request(self) -> None:
        rules = default_rules(default_channel="#ops")
        event = NormalizedEvent(
            source="github",
            event_type="pull_request",
            action="opened",
            title="Add new auth flow",
            actor="dev-user",
            entity_id="1234",
            url="https://github.com/org/repo/pull/1",
            payload={},
        )

        actions = select_actions(event, rules)
        self.assertGreaterEqual(len(actions), 2)
        self.assertEqual(actions[0].kind, "slack_message")
        self.assertEqual(actions[1].kind, "jira_issue")

    def test_selects_actions_for_new_supplier(self) -> None:
        rules = default_rules(default_channel="#ops")
        event = NormalizedEvent(
            source="platform",
            event_type="supplier.created",
            action="created",
            title="Shenzhen Precision Parts Co.",
            actor="Li Wei",
            entity_id="supplier-1",
            url="/suppliers/supplier-1",
            payload={},
        )

        actions = select_actions(event, rules)
        self.assertEqual([action.kind for action in actions], ["slack_message", "jira_issue"])

    def test_selects_actions_for_product_import(self) -> None:
        rules = default_rules(default_channel="#ops")
        event = NormalizedEvent(
            source="platform",
            event_type="products.imported",
            action="imported",
            title="12 products imported for Shenzhen Precision Parts Co.",
            actor="Shenzhen Precision Parts Co.",
            entity_id="supplier-1",
            url="/products?supplier_id=supplier-1",
            payload={},
        )

        actions = select_actions(event, rules)
        self.assertEqual([action.kind for action in actions], ["slack_message", "jira_issue"])

    def test_renders_templates(self) -> None:
        action = ActionSpec(
            kind="slack_message",
            params={"channel": "#alerts", "text": "New event {event_type} by {actor}"},
        )
        event = NormalizedEvent(
            source="github",
            event_type="issues",
            action="opened",
            title="Bug",
            actor="qa-user",
            entity_id="9",
            payload={},
        )

        rendered = render_action_params(action, event)
        self.assertEqual(rendered.params["text"], "New event issues by qa-user")


if __name__ == "__main__":
    unittest.main()
