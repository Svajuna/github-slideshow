import json
import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import init_db
from .dispatcher import Dispatcher
from .integrations.jira import JiraClient
from .integrations.linear import LinearClient
from .integrations.slack import SlackClient
from .parser import parse_event
from .routes import products_router, suppliers_router
from .rules import default_rules
from .schemas import WebhookResponse
from .security import WebhookVerifier

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Cloud Agent Webhook Processor", version="0.1.0")
settings = get_settings()
verifier = WebhookVerifier(settings)
dispatcher = Dispatcher(
    slack_client=SlackClient(token=settings.slack_bot_token),
    jira_client=JiraClient(
        base_url=settings.jira_base_url,
        email=settings.jira_email,
        api_token=settings.jira_api_token,
        project_key=settings.jira_project_key,
    ),
    linear_client=LinearClient(
        api_key=settings.linear_api_key,
        team_id=settings.linear_team_id,
    ),
    rules=default_rules(default_channel=settings.slack_default_channel),
)
app.state.dispatcher = dispatcher
app.include_router(suppliers_router)
app.include_router(products_router)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/{source}", response_model=WebhookResponse)
async def webhook_ingest(source: str, request: Request, background_tasks: BackgroundTasks) -> WebhookResponse:
    source = source.lower()
    body = await request.body()
    headers = {key.lower(): value for key, value in request.headers.items()}

    verifier.verify(source=source, headers=headers, body=body)

    if not body:
        raise HTTPException(status_code=400, detail="Empty webhook body")
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    # Slack URL verification handshake.
    if source == "slack" and payload.get("type") == "url_verification":
        return JSONResponse({"challenge": payload.get("challenge", "")})

    event = parse_event(source=source, payload=payload, headers=headers)
    actions = dispatcher.plan_actions(event)
    if not actions:
        return WebhookResponse(
            status="ignored",
            source=event.source,
            event_type=event.event_type,
            actions_count=0,
        )

    background_tasks.add_task(dispatcher.execute, actions)
    return WebhookResponse(
        status="accepted",
        source=event.source,
        event_type=event.event_type,
        actions_count=len(actions),
    )
