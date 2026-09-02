# Sales Coach AI — GCash Field Sales Intelligence Platform

An AI-powered coaching assistant for GCash's field sales team — Distributor Sales Personnel (DSPs), Sales Managers, and Admins. Built on **AWS** with **LangGraph** multi-agent orchestration and **Amazon Bedrock** (Claude 3 Sonnet).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI + Jinja2 UI                       │
│         (Role-based views: DSP / Manager / Admin)           │
├─────────────────────────────────────────────────────────────┤
│                   LangGraph Agent Graph                      │
│  Master → Intent → Profile/Ranking/Brief/Nudge → Response   │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Bedrock  │ Cognito  │   RDS    │   S3     │  CloudWatch     │
│ Claude 3 │  Auth    │PostgreSQL│ Storage  │  + X-Ray        │
│Guardrails│  JWKS    │ asyncpg  │          │  Observability  │
└──────────┴──────────┴──────────┴──────────┴─────────────────┘
```

### AWS Services Used

| Service | Purpose |
|---|---|
| **Amazon Bedrock** | LLM (Claude 3 Sonnet) + Guardrails for AI coaching |
| **Amazon Cognito** | User authentication & JWKS token verification |
| **Amazon RDS** | PostgreSQL database for all structured data |
| **Amazon S3** | File storage (transcripts, models, exports) |
| **Amazon DynamoDB** | Agent state checkpoints & session cache |
| **Amazon ElastiCache** | Redis caching for rankings & briefs |
| **Amazon SageMaker** | ML endpoint for merchant churn/propensity scoring |
| **Amazon CloudWatch** | Structured logging & custom metrics |
| **AWS X-Ray** | Distributed tracing across all services |
| **Amazon SNS** | Real-time alerts & notifications |
| **Amazon EventBridge** | Event-driven workflows |
| **AWS KMS** | PII encryption at rest |
| **AWS Secrets Manager** | Secure credential storage |
| **AWS CodeBuild** | CI/CD pipeline |

---

## Project Structure

```
salescoach-ai/
├── app/
│   ├── api/
│   │   ├── routes/          # FastAPI route handlers
│   │   │   ├── auth.py      # Cognito login/logout
│   │   │   ├── outlets.py   # Outlet CRUD & priority list
│   │   │   ├── briefs.py    # AI-generated briefs & area summary
│   │   │   ├── actions.py   # Action recommendations
│   │   │   ├── ask.py       # NL chat → LangGraph agent
│   │   │   ├── manager.py   # Manager dashboard & DSP metrics
│   │   │   ├── admin.py     # Admin dashboard, users, health
│   │   │   └── ui.py        # HTML page routes
│   │   └── dependencies.py  # Auth guards, DB session
│   ├── aws/                 # boto3 client wrappers
│   │   ├── bedrock_client.py
│   │   ├── cognito_client.py
│   │   ├── s3_client.py
│   │   ├── dynamodb_client.py
│   │   ├── cloudwatch_client.py
│   │   ├── sns_client.py
│   │   ├── kms_client.py
│   │   ├── xray_helpers.py
│   │   ├── secrets_client.py
│   │   ├── eventbridge_client.py
│   │   └── sagemaker_client.py
│   ├── db/
│   │   ├── session.py       # Async SQLAlchemy engine (asyncpg)
│   │   └── init_db.py       # Table creation
│   ├── middleware/
│   │   ├── audit.py         # CloudWatch audit logging
│   │   └── tenant.py        # Multi-tenant context injection
│   ├── models/              # 13 SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── ui/
│   │   ├── templates/       # Jinja2 HTML templates
│   │   └── static/          # CSS, JS assets
│   ├── config.py            # Pydantic Settings (from .env)
│   └── main.py              # FastAPI app entrypoint
├── agents/
│   ├── graph.py             # LangGraph StateGraph definition
│   ├── state.py             # AgentState TypedDict
│   ├── master_agent.py      # Orchestrator node
│   ├── intent_agent.py      # Intent classification (Bedrock)
│   ├── profile_agent.py     # Outlet data retrieval
│   ├── ranking_agent.py     # Priority ranking
│   ├── brief_agent.py       # AI brief generation (Bedrock)
│   ├── recommendation_agent.py
│   ├── nudge_agent.py
│   ├── nl_response_agent.py
│   ├── clarification_agent.py
│   ├── prompts/             # System prompts for each agent
│   └── tools/               # DB query & cache tools
├── data/
│   ├── csv/                 # 13 synthetic CSV datasets
│   ├── data_dictionary.yaml # Schema documentation
│   ├── generate_csv.py      # Dataset generator script
│   └── seed_rds.py          # RDS database seeder
├── knowledge_graph/         # Knowledge graph builder
├── .env.example             # Environment template (NO secrets)
├── requirements.txt         # Python dependencies
├── Dockerfile               # Production container
├── docker-compose.yml       # Docker orchestration
├── buildspec.yml            # AWS CodeBuild CI/CD
└── README.md                # This file
```

---

## Role-Based Access

| Role | Dashboard | Pages | Data Scope |
|---|---|---|---|
| **DSP** | Ranked outlet list | Ask | Own assigned outlets only |
| **Manager** | Area KPIs, DSP table | DSP Performance, Area Summary, Ask | All outlets in their area |
| **Admin** | System-wide stats | All Areas, Users, System Health, Ask | Everything |

### Demo Accounts

| Email | Role | Password |
|---|---|---|
| `dsp1@gcash.com` | DSP | `password` |
| `manager1@gcash.com` | Manager | `password` |
| `admin@gcash.com` | Admin | `password` |

---

## Setup & Deployment

### Prerequisites

- Python 3.11+
- AWS Account with the following services provisioned:
  - RDS PostgreSQL instance
  - Cognito User Pool
  - Bedrock model access (Claude 3 Sonnet)
  - S3 bucket
  - DynamoDB tables
- AWS CLI configured (`aws configure`)

### 1. Clone & Install

```bash
git clone <repo-url>
cd salescoach-ai
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your real AWS resource ARNs/IDs
```

> ⚠️ **NEVER commit `.env` to Git.** It contains secrets and API keys.

### 3. Seed the Database

```bash
python -m data.seed_rds
```

### 4. Run Locally (Connecting to AWS)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open: http://localhost:8000

### 5. Deploy to AWS (Docker → ECR → ECS)

```bash
# Build
docker build -t salescoach-ai .

# Tag & Push to ECR
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.ap-southeast-1.amazonaws.com
docker tag salescoach-ai:latest <account>.dkr.ecr.ap-southeast-1.amazonaws.com/salescoach-ai:latest
docker push <account>.dkr.ecr.ap-southeast-1.amazonaws.com/salescoach-ai:latest
```

---

## Dataset

13 synthetic CSV datasets with **73,000+** records of Philippine GCash field-sales data:

| Dataset | Rows | Description |
|---|---|---|
| `areas.csv` | 5 | Sales territories (NCR, Visayas, Mindanao) |
| `products.csv` | 10 | GCash products (Cash-In, GCredit, GSave, etc.) |
| `managers.csv` | 5 | Sales managers |
| `dsps.csv` | 40 | Field sales representatives |
| `merchants.csv` | 200 | Business owners (sari-sari stores, pharmacies) |
| `outlets.csv` | 708 | Store locations with GPS coordinates |
| `assignments.csv` | 708 | DSP ↔ Outlet mappings |
| `outlet_scores.csv` | 708 | AI priority scores & risk factors |
| `transactions.csv` | 50,000 | 90 days of GCash transactions (PHP) |
| `visit_logs.csv` | 16,840 | DSP field visit records |
| `action_recommendations.csv` | 500 | AI action items |
| `outlet_products.csv` | 3,872 | Product activations per outlet |
| `users.csv` | 46 | Login accounts |

See [`data/data_dictionary.yaml`](data/data_dictionary.yaml) for full schema documentation.

---

## Security

- All secrets stored in **AWS Secrets Manager** (not in code)
- PII encrypted with **AWS KMS**
- Auth via **Amazon Cognito** (JWKS token verification)
- **Bedrock Guardrails** prevent cross-tenant data leakage in LLM output
- Row-Level Security (RLS) on PostgreSQL
- `.env` file is in `.gitignore` — never committed

---

## License

Proprietary — GCash AI Squad Homework Assignment
