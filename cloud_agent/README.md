# Cloud Agent Integrations Skeleton (Python)

Šis modulis pateikia bazinę architektūrą tiekėjų / produktų platformai ir Cloud Agent'ui, kuris:

1. Registruoja Kinijos gamintojus (`Suppliers`) ir valdo jų produktus (`Products`).
2. Importuoja produktus per API ir saugo juos SQLAlchemy/PostgreSQL duomenų modelyje.
3. Priima webhook įvykius iš GitHub / Slack / Jira / Linear.
4. Normalizuoja išorinius ir vidinius platformos įvykius į vieną formatą.
5. Pritaiko taisykles (rule engine).
6. Atlieka veiksmus: pranešimai į Slack, užduočių kūrimas Jira arba Linear.

## Struktūra

```text
cloud_agent/
  app/
    main.py            # FastAPI entrypoint
    config.py          # Env konfigūracija
    database.py        # SQLAlchemy engine/session ir lentelių inicializacija
    models.py          # Supplier/Product ORM modeliai
    platform_schemas.py # Pydantic API schemos tiekėjams ir produktams
    platform_events.py # Supplier/Product domeno įvykiai -> Cloud Agent actions
    security.py        # Webhook parašų tikrinimas
    parser.py          # Provider payload -> NormalizedEvent
    rules.py           # Taisyklių variklis
    dispatcher.py      # Action vykdymas
    schemas.py         # Bendri modeliai
    routes/
      suppliers.py     # Supplier registracija ir profilio valdymas
      products.py      # Product CRUD ir importo API
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

Konfigūruojant PostgreSQL naudokite:

```bash
AGENT_DATABASE_URL=postgresql+psycopg://agent:agent@localhost:5432/cloud_agent
```

Lokaliai, jei `AGENT_DATABASE_URL` nepateiktas, naudojamas `sqlite:///./cloud_agent.db`.

## Platformos API endpointai

Tiekėjai:

- `POST /suppliers` - registruoti naują tiekėją ir paleisti `supplier.created` automatizaciją.
- `GET /suppliers` - tiekėjų sąrašas.
- `GET /suppliers/{supplier_id}` - tiekėjo profilis.
- `PATCH /suppliers/{supplier_id}` - atnaujinti tiekėjo profilį.

Produktai:

- `POST /products` - sukurti vieną produktą.
- `GET /products` - produktų sąrašas, galima filtruoti pagal `supplier_id` ir `product_status`.
- `GET /products/{product_id}` - produkto informacija.
- `PATCH /products/{product_id}` - atnaujinti produktą.
- `DELETE /products/{product_id}` - pašalinti produktą.
- `POST /products/import` - importuoti produktų sąrašą ir paleisti `products.imported` automatizaciją.

Webhook endpointai:

- `POST /webhooks/github`
- `POST /webhooks/slack`
- `POST /webhooks/jira`
- `POST /webhooks/linear`

Vidiniai platformos įvykiai:

- `supplier.created` - siunčia Slack pranešimą ir sukuria Jira užduotį tiekėjo patikrai.
- `products.imported` - siunčia Slack pranešimą ir sukuria Jira užduotį produktų importo validacijai.

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
