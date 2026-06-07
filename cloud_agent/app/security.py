import hashlib
import hmac
import time

from fastapi import HTTPException, status

from .config import Settings


def _header(headers: dict[str, str], key: str) -> str:
    return headers.get(key.lower(), "")


class WebhookVerifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def verify(self, source: str, headers: dict[str, str], body: bytes) -> None:
        if source == "github":
            self._verify_github(headers, body)
            return
        if source == "slack":
            self._verify_slack(headers, body)
            return
        if source == "jira":
            self._verify_shared_token(headers, self.settings.jira_webhook_token)
            return
        if source == "linear":
            self._verify_shared_token(headers, self.settings.linear_webhook_token)
            return
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported source")

    def _verify_github(self, headers: dict[str, str], body: bytes) -> None:
        secret = self.settings.github_webhook_secret
        if not secret:
            return
        signature = _header(headers, "x-hub-signature-256")
        if not signature:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature")
        digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        expected = f"sha256={digest}"
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    def _verify_slack(self, headers: dict[str, str], body: bytes) -> None:
        secret = self.settings.slack_signing_secret
        if not secret:
            return
        timestamp = _header(headers, "x-slack-request-timestamp")
        signature = _header(headers, "x-slack-signature")
        if not timestamp or not signature:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Slack headers")

        if abs(time.time() - int(timestamp)) > 60 * 5:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stale Slack request")

        base = f"v0:{timestamp}:{body.decode('utf-8')}"
        digest = hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest()
        expected = f"v0={digest}"
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Slack signature")

    @staticmethod
    def _verify_shared_token(headers: dict[str, str], expected_token: str) -> None:
        if not expected_token:
            return
        actual = _header(headers, "x-webhook-token")
        if not hmac.compare_digest(actual, expected_token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook token")
