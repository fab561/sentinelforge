# SentinelForge

**SOC Automation Platform (SOAR)** — automates L1/L2 analyst workflows: alert triage, IOC enrichment, automated threat response, and incident case management.

## Architecture

| Module | Owner | Description |
|--------|-------|-------------|
| **M1: SIEM Core & Data Pipeline** | Farhad | Wazuh 4.14.4, FastAPI backend, PostgreSQL, Redis queue |
| **M2: Threat Intel & Enrichment** | Kunal | VT, AbuseIPDB, GreyNoise, OTX — scoring & auto-verdict |
| **M3: Playbook Engine & Response** | Tathagata | YAML playbooks, Celery, Cloudflare IP blocking |
| **M4: Frontend Dashboard** | Chandrakant | Next.js, shadcn/ui, dark SOC dashboard |
| **M5: Raspberry Pi Honeypot** | Ayush | Cowrie SSH honeypot, Wazuh agent on RPi |

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/fab561/sentinelforge.git
cd sentinelforge
cp .env.example .env  # edit passwords as needed

# 2. Start all services
docker compose up -d

# 3. Seed sample data (20 alerts, 3 cases, 2 rules)
docker compose exec backend python -m seed

# 4. Access
# Backend API:      http://localhost:8000/api/
# API docs:         http://localhost:8000/docs
# Wazuh Dashboard:  http://localhost:5601
# Health check:     http://localhost:8000/health
```

## API Endpoints

| Endpoint | Method | Consumer | Purpose |
|----------|--------|----------|---------|
| `/api/alerts` | GET | M2, M4 | Fetch alerts (paginated, filterable) |
| `/api/alerts/{id}` | PATCH | M2, M3 | Update enrichment, verdict, actions |
| `/api/alerts/queue/next` | GET | M2 | Pop next un-enriched alert from Redis |
| `/api/cases` | GET/POST | M4 | CRUD for incident cases |
| `/api/cases/{id}` | GET/PATCH | M4 | Case detail & updates |
| `/api/rules` | GET/POST | M4 | CRUD for detection rules |
| `/api/rules/{id}` | PATCH/DELETE | M4 | Update/delete rules |
| `/api/stats` | GET | M4 | Dashboard metrics |
| `/api/wazuh/agents` | GET | M4, M5 | List connected Wazuh agents |

## Tech Stack

- **SIEM:** Wazuh 4.14.4 (Manager + Indexer + Dashboard)
- **Backend:** Python FastAPI, SQLAlchemy async, Alembic
- **Database:** PostgreSQL 16
- **Queue/Cache:** Redis 7
- **Frontend:** Next.js + React + Tailwind v4 + shadcn/ui (Module 4)
- **Honeypot:** Cowrie SSH on Raspberry Pi (Module 5)
- **Firewall:** Cloudflare free tier IP blocking (Module 3)
- **Containerization:** Docker Compose

## Project Structure

```
sentinelforge/
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Environment template
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── seed.py                 # Sample data seeder
│   ├── alembic/                # DB migrations
│   └── app/
│       ├── main.py             # FastAPI entry point
│       ├── core/               # Config, DB, Redis, Wazuh clients
│       ├── models/             # SQLAlchemy models
│       ├── schemas/            # Pydantic request/response
│       ├── api/                # REST API routers
│       ├── services/           # Business logic
│       └── ingestion/          # Wazuh poller, normalizer, queue
├── wazuh/
│   └── custom_rules/           # SentinelForge Wazuh detection rules
├── playbooks/                  # Module 3: YAML playbooks
└── frontend/                   # Module 4: Next.js dashboard
```

## Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| SentinelForge API | admin | admin123 |
| Wazuh API | wazuh-wui | MyS3cr3tP4ssw0rd! |

## Team

Built as a college capstone project — zero budget, all free/open-source tools.
