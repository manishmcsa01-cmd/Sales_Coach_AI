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
| **Amazon ECR** | Docker container registry |
| **Amazon ECS (Fargate)** | Serverless container orchestration |
| **AWS CodeBuild** | CI/CD pipeline |

---

## Project Structure

```
salescoach-ai/
├── app/
│   ├── api/
│   │   ├── routes/              # FastAPI route handlers
│   │   │   ├── auth.py          # Cognito login/logout
│   │   │   ├── outlets.py       # Outlet CRUD & priority list
│   │   │   ├── briefs.py        # AI-generated briefs & area summary
│   │   │   ├── ask.py           # NL chat → LangGraph agent
│   │   │   ├── manager.py       # Manager dashboard & DSP metrics
│   │   │   ├── admin.py         # Admin dashboard, users, health
│   │   │   └── ui.py            # HTML page routes
│   │   └── dependencies.py      # Auth guards, DB session
│   ├── aws/                     # boto3 client wrappers (12 files)
│   ├── db/                      # Async SQLAlchemy (asyncpg)
│   ├── middleware/               # Audit logging, tenant context
│   ├── models/                  # 13 SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── ui/
│   │   ├── templates/           # Jinja2 HTML templates
│   │   └── static/              # CSS, JS assets
│   ├── config.py                # Pydantic Settings (from .env)
│   └── main.py                  # FastAPI app entrypoint
├── agents/
│   ├── graph.py                 # LangGraph StateGraph definition
│   ├── state.py                 # AgentState TypedDict
│   ├── master_agent.py          # Orchestrator node
│   ├── intent_agent.py          # Intent classification (Bedrock)
│   ├── profile_agent.py         # Outlet data retrieval
│   ├── ranking_agent.py         # Priority ranking
│   ├── brief_agent.py           # AI brief generation (Bedrock)
│   ├── recommendation_agent.py  # Personalized recommendations
│   ├── nudge_agent.py           # Smart nudges
│   ├── nl_response_agent.py     # Natural language formatting
│   ├── clarification_agent.py   # Clarifying questions
│   ├── prompts/                 # System prompts per agent
│   └── tools/                   # DB query & cache tools
├── data/
│   ├── csv/                     # 13 synthetic CSV datasets
│   ├── data_dictionary.yaml     # Schema documentation
│   ├── generate_csv.py          # Dataset generator script
│   └── seed_rds.py              # RDS database seeder
├── knowledge_graph/             # Knowledge graph builder
├── Dockerfile                   # Multi-stage production build
├── .dockerignore                # Excludes secrets from image
├── docker-compose.yml           # Local dev with PostgreSQL + Redis
├── ecs-task-definition.json     # ECS Fargate task definition
├── buildspec.yml                # AWS CodeBuild CI/CD
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template (NO secrets)
├── .gitignore                   # Blocks secrets from Git
└── README.md                    # This file
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

## Deployment

### Option 1: Docker Compose (Local Dev / Staging)

Spins up the app with local PostgreSQL and Redis containers.

```bash
# 1. Configure
cp .env.example .env
# Edit .env with your AWS credentials (Bedrock, Cognito, etc.)

# 2. Build & Run
docker-compose up --build -d

# 3. Seed database
docker-compose exec app python -m data.seed_rds

# 4. Access
open http://localhost:8000
```

---

### Option 2: AWS ECR + ECS Fargate (Production)

Full cloud deployment with containerized Fargate tasks.

#### Step 1: Create ECR Repository

```bash
aws ecr create-repository \
    --repository-name salescoach-ai \
    --region ap-southeast-1 \
    --image-scanning-configuration scanOnPush=true
```

#### Step 2: Build & Push Docker Image

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region ap-southeast-1 | \
    docker login --username AWS --password-stdin \
    <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com

# Build the image
docker build -t salescoach-ai .

# Tag for ECR
docker tag salescoach-ai:latest \
    <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/salescoach-ai:latest

# Push to ECR
docker push \
    <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/salescoach-ai:latest
```

#### Step 3: Store Secrets in AWS Secrets Manager

```bash
# Store each secret (repeat for all config values)
aws secretsmanager create-secret \
    --name salescoach/database-url \
    --secret-string "postgresql+asyncpg://user:pass@rds-endpoint:5432/salescoach_db" \
    --region ap-southeast-1

aws secretsmanager create-secret \
    --name salescoach/secret-key \
    --secret-string "your-production-secret-key" \
    --region ap-southeast-1

aws secretsmanager create-secret \
    --name salescoach/cognito-pool-id \
    --secret-string "ap-southeast-1_XXXXXXXXX" \
    --region ap-southeast-1

# Repeat for: cognito-client-id, bedrock-guardrail-id, s3-bucket,
#              sns-topic-arn, kms-key-id, redis-url
```

#### Step 4: Create ECS Cluster & Service

```bash
# Create cluster
aws ecs create-cluster \
    --cluster-name salescoach-cluster \
    --capacity-providers FARGATE \
    --region ap-southeast-1

# Register task definition
# (Edit ecs-task-definition.json — replace <ACCOUNT_ID> with your AWS account ID)
aws ecs register-task-definition \
    --cli-input-json file://ecs-task-definition.json \
    --region ap-southeast-1

# Create service with ALB
aws ecs create-service \
    --cluster salescoach-cluster \
    --service-name salescoach-service \
    --task-definition salescoach-ai \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
    --region ap-southeast-1
```

#### Step 5: Access Your App

After the ECS service starts, you can access via:
- **Public IP** of the Fargate task (if `assignPublicIp=ENABLED`)
- **ALB DNS** if you configured a load balancer (recommended)

---

### Docker Image Details

| Property | Value |
|---|---|
| **Base Image** | `python:3.11-slim` |
| **Build** | Multi-stage (builder + production) |
| **User** | Non-root `appuser` (security) |
| **Port** | 8000 |
| **Health Check** | `curl http://localhost:8000/docs` every 30s |
| **Workers** | 2 Uvicorn workers |
| **Image Size** | ~250 MB |

### Files Excluded from Docker Image (via `.dockerignore`)

| Excluded | Reason |
|---|---|
| `.env`, `.env.*` | Secrets — injected at runtime via ECS/Secrets Manager |
| `*.db`, `*.sqlite` | Database files — RDS is used in production |
| `__pycache__/`, `*.pyc` | Build artifacts |
| `.git/`, `.vscode/` | Dev tooling |
| `test_*.py`, `fix_*.py` | Dev scripts |
| `local_storage/` | Mock AWS data |

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
| `assignments.csv` | 708 | DSP-Outlet mappings |
| `outlet_scores.csv` | 708 | AI priority scores & risk factors |
| `transactions.csv` | 50,000 | 90 days of GCash transactions (PHP) |
| `visit_logs.csv` | 16,840 | DSP field visit records |
| `action_recommendations.csv` | 500 | AI action items |
| `outlet_products.csv` | 3,872 | Product activations per outlet |
| `users.csv` | 46 | Login accounts |

See [`data/data_dictionary.yaml`](data/data_dictionary.yaml) for full schema documentation.

---

## Security

- **No secrets in code** — all credentials via Secrets Manager or `.env` (gitignored)
- PII encrypted with **AWS KMS**
- Auth via **Amazon Cognito** (JWKS token verification)
- **Bedrock Guardrails** prevent data leakage in LLM output
- Row-Level Security (RLS) on PostgreSQL
- Docker runs as **non-root user**
- `.dockerignore` excludes `.env`, credentials, and dev files from image
- ECR **image scanning** enabled on push

---

## License

Proprietary — GCash AI Squad Homework Assignment
