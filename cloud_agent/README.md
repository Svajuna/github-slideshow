# Cloud Agent Integrations Skeleton (Python)

Šis modulis pateikia bazinę architektūrą Cloud Agent'ui, kuris:

1. Priima webhook įvykius iš GitHub / Slack / Jira / Linear.
2. Normalizuoja įvykius į vieną vidinį formatą.
3. Pritaiko taisykles (rule engine).
4. Atlieka veiksmus: pranešimai į Slack, užduočių kūrimas Jira arba Linear.

## Struktūra

```text
cloud_agent/
  app/
    main.py            # FastAPI entrypoint
    config.py          # Env konfigūracija
    security.py        # Webhook parašų tikrinimas
    parser.py          # Provider payload -> NormalizedEvent
    rules.py           # Taisyklių variklis
    dispatcher.py      # Action vykdymas
    schemas.py         # Bendri modeliai
    integrations/
      base.py
      slack.py
      jira.py
      linear.py
  tests/
    test_rules.py
  .env.example
  requirements.txt
```

## Paleidimas lokaliai

```bash
cd cloud_agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

Webhook endpointai:

- `POST /webhooks/github`
- `POST /webhooks/slack`
- `POST /webhooks/jira`
- `POST /webhooks/linear`

## Rekomenduojama architektūra (production)

- **Ingress API** (šis FastAPI servisas): validuoja parašus ir normalizuoja payload.
- **Event Queue** (pvz. SQS / RabbitMQ / Kafka): atskiria webhook priėmimą nuo veiksmų vykdymo.
- **Rule/Workflow Worker**: taiko taisykles ir sprendžia kokius veiksmus vykdyti.
- **Action Workers**: atskiri workeriai Slack/Jira/Linear, su retry + dead-letter queue.
- **Observability**: centralizuoti logai, request-id/correlation-id, metrikos, alerting.

Tokiu būdu sistema išlieka:

- atspari šuoliniam webhook srautui,
- lengvai plečiama naujoms integracijoms,
- aiškiai audituojama (įvykis -> taisyklė -> veiksmas).
