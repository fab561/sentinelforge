# SentinelForge

[![ci](https://github.com/fab561/sentinelforge/actions/workflows/ci.yml/badge.svg)](https://github.com/fab561/sentinelforge/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js)
![wazuh](https://img.shields.io/badge/Wazuh-4.14-1B4F8B)
![docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![license](https://img.shields.io/badge/license-MIT-green)

**Open-source SOC Automation Platform (SOAR).** Replaces ~$100k/yr commercial
tooling (Splunk SOAR, Cortex XSOAR) with free + open-source components for
small SOCs, MSSPs, university labs, and CTF teams.

Detects an attack with Wazuh, enriches it against four threat-intel feeds,
runs a YAML-defined playbook to block + open a case, harvests evidence
from a Cowrie honeypot, and surfaces it all in a Next.js dashboard — in
under 15 seconds, fully automated.

---

## What you get

| Capability | Page | Status |
|---|---|---|
| Live alert ingestion (Wazuh poller) | `/alerts` | Working |
| Real threat-intel enrichment (VT + AbuseIPDB + GreyNoise + OTX) | `/alerts/[id]` | Working |
| Auto-verdict + threat scoring | dashboard cards | Working |
| YAML-defined playbook engine + dry-run | `/playbooks` | Working |
| Cloudflare edge IP blocking | playbook action | Working |
| Wazuh active-response (host firewall, account disable, isolate) | playbook action | Working |
| Auto-correlation — duplicate alerts collapse into one case | `/cases/[id]` | Working |
| MITRE ATT&CK coverage heatmap | `/mitre` | Working |
| Case lifecycle + MTTA/MTTR SLA charts | `/dashboard` | Working |
| Analyst-curated IOC watchlist (re-uses past intel) | `/iocs` | Working |
| Evidence attachments (PCAPs, Cowrie sessions) — MinIO + sha256 dedup | `/cases/[id]` | Working |
| Cowrie session-log auto-attach to honeypot cases | playbook hook | Working |
| Audit log of every case + evidence mutation | `/audit` | Working |
| PDF case export (forensic-style report) | case detail | Working |
| Per-IP API rate limiting | backend | Working |
| Light / dark / system theme | sidebar | Working |
| 30 Wazuh rules across 10 MITRE tactics | `/rules` | Working |
| pytest + GitHub Actions CI | `tests/`, `.github/` | Working |

---

## Architecture

```mermaid
flowchart LR
  attacker((Attacker))
  cowrie[Cowrie<br/>SSH honeypot]
  agent[Wazuh<br/>agent]
  manager[Wazuh<br/>manager]
  poller[M1<br/>poller]
  pg[(Postgres)]
  redis[(Redis)]
  m2[M2 enrichment<br/>worker]
  m3[M3 playbook<br/>worker]
  api[FastAPI<br/>backend]
  ui[Next.js<br/>dashboard]
  minio[(MinIO<br/>evidence)]
  cf[Cloudflare]
  vt[VT / AbuseIPDB<br/>GreyNoise / OTX]

  attacker -->|ssh :2222| cowrie
  cowrie -->|json log| agent
  agent -->|:1514| manager
  manager -->|alerts.json| poller
  poller --> pg
  poller -->|alert_id| redis
  redis --> m2
  m2 -->|lookup| vt
  m2 -->|verdict + tags| pg
  m2 -->|alert_id| redis
  redis --> m3
  m3 -->|create case| pg
  m3 -->|harvest events| minio
  m3 -->|block ip| cf
  m3 -->|active-response| manager
  api --> pg
  api --> minio
  ui -->|REST| api
```

End-to-end flow from "attacker hits the trap" to "analyst sees the
auto-resolved case with attached evidence" runs in roughly 15 seconds.

---

## Modules

| # | Module | Owner | Description |
|---|---|---|---|
| M1 | SIEM Core & Data Pipeline | Farhad (lead) | Wazuh poller, FastAPI, Postgres, Redis, alert correlation, audit log, PDF export, rate limiting |
| M2 | Threat Intel & Enrichment | Kunal | 4 free TI providers, weighted scoring, IOC watchlist |
| M3 | Playbook Engine & Response | Tathagata | YAML engine, dry-run, 6 action types (notify, block_ip, wazuh_active_response, create_case, tag_alert, update_status) |
| M4 | Frontend Dashboard | Chandrakant | Next.js 16, shadcn/ui, dark/light theme, 10 pages, MITRE heatmap, MTTR charts |
| M5 | Honeypot | Ayush | Cowrie SSH honeypot, Wazuh agent, session-log auto-attach to cases |

---

## Installation

### Prerequisites

| Tool | Version | Why |
|---|---|---|
| Docker Desktop (Windows / macOS) **or** Docker Engine + Compose v2 (Linux) | 24+ | Runs the 11-container stack |
| Node.js | 20+ | Frontend dev server (M4) |
| Git | any | Clone |
| ~6 GB free disk | — | Wazuh + OpenSearch images are large |
| ~6 GB free RAM | — | OpenSearch alone wants 1 GB JVM heap |

### Step 1 — clone and configure

```bash
git clone https://github.com/fab561/sentinelforge.git
cd sentinelforge

# Copy the env template. Defaults work for local lab; only the threat-intel
# API keys must be filled in to see enrichment fire on real IPs.
cp .env.example .env
```

Open `.env` and add your **free** API keys (sign-up links below in
[API keys](#api-keys-free-tiers)). VirusTotal + AbuseIPDB + OTX are
the minimum useful set; GreyNoise is optional (50/day free tier is
stingy).

```ini
VIRUSTOTAL_API_KEY=...
ABUSEIPDB_API_KEY=...
OTX_API_KEY=...
GREYNOISE_API_KEY=          # optional
```

### Step 2 — start the backend stack

```bash
docker compose up -d
```

First boot pulls roughly 3 GB of images and takes ~5 minutes. The
backend auto-creates tables and seeds **30 rules + 20 sample alerts +
3 cases** on first start — no manual seed step.

Watch the stack come up:

```bash
docker compose ps
# Expect 11 containers all "Up", including:
#   sf-wazuh-indexer, sf-wazuh-manager, sf-wazuh-dashboard, sf-wazuh-agent
#   sf-cowrie, sf-postgres, sf-redis, sf-minio
#   sf-backend, sf-enrichment-worker, sf-playbook-worker
```

Wait until the backend health check responds:

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"sentinelforge-backend"}
```

### Step 3 — start the frontend dev server

In a **separate terminal**:

```bash
cd frontend
npm install        # one-time
npm run dev        # serves on http://localhost:3000
```

### Step 4 — verify the pipeline works

Inject a test alert with a known-bad IP and watch it flow through
enrichment → playbook → case:

```bash
docker exec sf-backend python -c "
import asyncio, json, uuid
from datetime import datetime, timezone
from app.core.database import async_session
from app.core.redis import get_redis, close_redis
from app.models.alert import Alert
async def go():
    aid=f'sanity-{uuid.uuid4().hex[:6]}'
    async with async_session() as db:
        db.add(Alert(alert_id=aid, timestamp=datetime.now(timezone.utc),
            source='manual-test', severity='critical', category='honeypot',
            title='Sanity check: known-bad IP',
            observables={'source_ip':'185.220.101.1'},
            raw_log='', status='new'))
        await db.commit()
    r=await get_redis()
    await r.lpush('alerts:pending_enrichment', json.dumps({
        'alert_id':aid,'observables':{'source_ip':'185.220.101.1'},
        'severity':'critical','category':'honeypot','source':'cowrie',
        'title':'Sanity'}))
    await close_redis()
    print('injected:',aid)
asyncio.run(go())
"
```

Open http://localhost:3000/alerts after ~10 s — the alert should be
enriched with `verdict=suspicious` or `malicious` and tagged from
VT / AbuseIPDB / OTX. A new case appears at http://localhost:3000/cases.

---

## Access URLs

All services bind to `localhost` on the host machine. Make sure no other
process is using these ports before `docker compose up`.

| # | Service | URL | Port | What it is |
|---|---|---|---|---|
| 1 | **SentinelForge dashboard (M4)** | http://localhost:3000 | 3000 | Main analyst UI — start here |
| 2 | **Backend API** | http://localhost:8000 | 8000 | FastAPI — REST endpoints |
| 3 | **API docs (Swagger UI)** | http://localhost:8000/docs | 8000 | Auto-generated, try-it-out |
| 4 | **Backend health** | http://localhost:8000/health | 8000 | `{"status":"ok"}` when ready |
| 5 | **Wazuh dashboard** | http://localhost:5601 | 5601 | OpenSearch UI for raw alerts |
| 6 | **Wazuh dashboard — direct app** | http://localhost:5601/app/wz-home | 5601 | Wazuh app entry (4.14 renamed `/app/wazuh` → `/app/wz-home`) |
| 7 | **Wazuh indexer (OpenSearch)** | http://localhost:9200 | 9200 | REST API for raw indices |
| 8 | **Wazuh manager API** | https://localhost:55000 | 55000 | Self-signed cert; `-k` to curl |
| 9 | **MinIO S3 API** | http://localhost:9100 | 9100 | Programmatic access to evidence bucket |
| 10 | **MinIO console** | http://localhost:9101 | 9101 | Web UI for the evidence bucket |
| 11 | **Cowrie SSH (honeypot)** | `ssh -p 2222 root@localhost` | 2222 | Connections logged + auto-attached to cases |
| 12 | **Postgres (direct)** | `psql -h localhost -p 5432 -U sf_admin sentinelforge` | 5432 | Use only for debugging |
| 13 | **Redis (direct)** | `redis-cli -h localhost -p 6379` | 6379 | Use only for debugging |

### Frontend pages

Once you're at http://localhost:3000, the sidebar links to:

| Path | What it shows |
|---|---|
| `/dashboard` | Stat cards (alerts, cases, agents), severity + verdict breakdown, MTTA/MTTR + 14-day SLA trend, recent alerts/cases, top categories |
| `/alerts` | Paginated alert list with filter chips (severity, status) |
| `/alerts/[alert_id]` | Alert detail — observables, MITRE, enrichment JSON, playbook actions, raw log |
| `/cases` | Paginated case list |
| `/cases/[id]` | Case detail — correlated alerts, evidence panel (upload + download), Export PDF button |
| `/rules` | All 30 detection rules (Wazuh + Sigma) |
| `/playbooks` | YAML playbook cards + dry-run panel |
| `/iocs` | IOC watchlist — add / toggle / delete indicators |
| `/mitre` | ATT&CK coverage heatmap (14 tactics × techniques observed) |
| `/agents` | Wazuh agent status |
| `/audit` | Audit log with filter chips |

---

## Credentials

**Lab use only — change every value below before exposing this stack
to the internet.** All defaults live in `.env.example` and are read
from `.env` at boot.

| Service | Username | Password | Set via |
|---|---|---|---|
| **SentinelForge admin** (seeded) | `admin@sentinelforge.local` (or `admin`) | `admin123` | `seed.py` (idempotent — won't re-seed) |
| **Wazuh manager API** | `wazuh-wui` | `MyS3cr3tP4ssw0rd!` | `WAZUH_API_USER` / `WAZUH_API_PASSWORD` |
| **Wazuh indexer (OpenSearch)** | _security plugin disabled_ | — | `wazuh/indexer/opensearch.yml` |
| **Wazuh dashboard** | _security plugin stripped at boot_ | — | docker-compose entrypoint |
| **Postgres** | `sf_admin` | `changeme` | `POSTGRES_USER` / `POSTGRES_PASSWORD` |
| **MinIO root** | `sf_admin` | `changeme-minio-pw` | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| **MinIO access key** (backend → MinIO) | `sf_admin` | `changeme-minio-pw` | `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` |
| **JWT secret** (NextAuth — currently unused, prepared for future auth) | n/a | `changeme-in-production` | `SECRET_KEY` |
| **Cowrie SSH honeypot** | `root` (or any) | many work, most fail — that's the point | hardcoded in cowrie's default `userdb` |

### Threat-intel API keys (you supply)

Free tiers are sufficient for development; see [API keys](#api-keys-free-tiers).

| Provider | Env var |
|---|---|
| VirusTotal | `VIRUSTOTAL_API_KEY` |
| AbuseIPDB | `ABUSEIPDB_API_KEY` |
| GreyNoise (Community) | `GREYNOISE_API_KEY` |
| AlienVault OTX | `OTX_API_KEY` |
| Cloudflare (optional, for `block_ip` action) | `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ZONE_ID` |

After editing `.env`, **recreate** the affected containers (a plain
restart doesn't re-substitute env vars):

```bash
docker compose up -d --force-recreate backend enrichment-worker playbook-worker
```

### Known quirks

- **Wazuh dashboard auth-token error popup**: the wazuh plugin
  occasionally surfaces `AxiosError: Error getting the authorization
  token` on the home screen. The plugin polls the manager API every
  10 s; if the manager is mid-restart or the API token cache expired,
  the popup briefly appears. Dismiss it — the underlying alert flow
  is unaffected. SentinelForge's own UI on http://localhost:3000
  reads its own DB and is independent.
- **Cowrie passwords**: the default Cowrie userdb permits a small set
  (`root/root`, `root/12345`, etc.) and rejects everything else.
  Connection events are still logged for failed attempts — the
  evidence harvester captures them either way. Customise via a
  `userdb.txt` baked into a custom Cowrie image if you need more.

---

<a id="api-keys-free-tiers"></a>
## API keys (free tiers)

All four providers offer free tiers ample for development:

| Provider | Free tier | Sign-up |
|---|---|---|
| VirusTotal | 500 lookups/day | https://www.virustotal.com/gui/join-us |
| AbuseIPDB | 1,000 checks/day | https://www.abuseipdb.com/register |
| GreyNoise (Community) | 50 lookups/day | https://viz.greynoise.io/signup |
| AlienVault OTX | unlimited (~10 req/s) | https://otx.alienvault.com/signup |

Drop them into `.env`:

```
VIRUSTOTAL_API_KEY=...
ABUSEIPDB_API_KEY=...
GREYNOISE_API_KEY=...
OTX_API_KEY=...
```

Then `docker compose up -d --force-recreate enrichment-worker` to load.

---

## Demo flow

What happens in a 90-second demo:

1. SSH-bruteforce the honeypot from any machine: `ssh -p 2222 root@<host>`.
2. Cowrie logs the attempt, Wazuh agent ships it, M1 poller picks it up,
   alert lands in Postgres + Redis.
3. M2 worker hits VT / AbuseIPDB / OTX in parallel — verdict in ~10s.
4. If verdict is malicious or critical: M3 playbook fires — Cloudflare
   block (if configured), Wazuh active-response on the host, case opens
   automatically, status set to `escalated`.
5. M3 cowrie evidence harvester scans cowrie.json + tty replays for the
   attacker IP, uploads them to MinIO, attaches to the new case.
6. Analyst opens `/cases/<id>` — sees the alert, the threat intel tags,
   the playbook actions taken, the attached evidence ready for download.
7. Click **Export PDF** for a forensic-style report ready to attach to a
   ticket.
8. Subsequent alerts from the same IP correlate into the existing case
   instead of opening duplicates.

---

## Detection coverage

29 custom Wazuh rules covering 10 MITRE ATT&CK enterprise tactics:

| Tactic | Rule IDs | Examples |
|---|---|---|
| Reconnaissance | 100250–100251 | port scan, scanner-tool invocation |
| Initial Access | 100252–100253 | web shell upload, external SSH login |
| Execution | 100220–100221, 100202 | wget/curl + chmod, downloaded file exec, cowrie commands |
| Persistence | 100254–100257 | cron, authorized_keys, new user, systemd unit |
| Privilege Escalation | 100230–100231 | sudo failures, failed su |
| Defense Evasion | 100260–100263 | Wazuh tampered, log cleared, firewall flushed, history wiped |
| Credential Access | 100210–100211, 100270 | brute force, distributed brute force, /etc/shadow read |
| Discovery | 100250 | port scan |
| Command & Control | 100280–100281 | reverse shell, base64 obfuscation |
| Impact | 100290–100291 | cryptominer, destructive command |

Plus 4 honeypot-specific rules (100200–100203) and 2 file-integrity rules
(100240–100241). Full list in [`wazuh/custom_rules/sentinelforge_rules.xml`](wazuh/custom_rules/sentinelforge_rules.xml).

---

## Tech stack

- **SIEM:** Wazuh 4.14 (manager + indexer + dashboard) on OpenSearch 2.19
- **Honeypot:** Cowrie (emulated SSH, full session capture)
- **Backend:** FastAPI 0.115, SQLAlchemy 2 async, Alembic, Pydantic v2
- **DB:** PostgreSQL 16 with JSONB for observables / enrichment
- **Queue:** Redis 7
- **Object storage:** MinIO (S3 API), bucket per environment, sha256-keyed
- **Threat intel:** VirusTotal, AbuseIPDB, GreyNoise, AlienVault OTX
- **Playbook engine:** PyYAML + asyncio, no Celery dependency
- **Frontend:** Next.js 16 App Router, React 19, Tailwind v4, shadcn/ui, recharts, lucide-react
- **PDF:** fpdf2 (pure-Python wheel, no system deps)
- **Rate limiting:** slowapi (in-process; swap to Redis backend at scale)
- **Tests:** pytest + pytest-asyncio
- **CI:** GitHub Actions (backend pytest + frontend tsc/lint/build + compose validate)
- **Container orchestration:** Docker Compose v2

---

## Project layout

```
sentinelforge/
  .github/workflows/ci.yml       # backend / frontend / compose CI jobs
  docker-compose.yml             # 11 services, 1 network
  .env.example                   # config template
  playbooks/                     # YAML playbook definitions (4 included)
  wazuh/
    custom_rules/                # 29 SOC detection rules (XML)
    indexer/, dashboard/         # OpenSearch + dashboard config (security off)
  backend/
    Dockerfile, requirements.txt
    seed.py                      # initial data
    seed_rules.py                # idempotent rule re-sync
    alembic/                     # migrations
    tests/                       # pytest suite (21 tests)
    app/
      main.py
      core/                      # config, db, redis, storage, rate_limit, wazuh
      models/                    # SQLAlchemy: alerts, cases, evidence, iocs, rules, audit, users
      schemas/                   # Pydantic request/response
      services/                  # business logic
      api/                       # FastAPI routers
      ingestion/                 # Wazuh poller + normalizer + Redis queue
      enrichment/                # M2 worker + 4 providers + scoring + cache
      playbook/                  # M3 engine + worker + 6 actions
  frontend/                      # M4 — Next.js 16 dashboard
    app/                         # 10 pages
    components/                  # shadcn/ui + custom (EvidencePanel, ThemeToggle, ...)
    lib/                         # api client, types, mitre reference
  m5/
    cowrie/                      # honeypot config
    wazuh-agent/                 # Wazuh agent Dockerfile
```

---

## Development

```bash
# Run the backend test suite (21 tests, ~1.3s)
docker exec sf-backend pytest tests/ -v

# Backend syntax check (CI also runs this)
docker exec sf-backend python -m compileall -q app

# Frontend typecheck + lint
cd frontend && npx tsc --noEmit && npx eslint . --ext .ts,.tsx

# Validate playbook YAML and Wazuh rule XML
python - <<'PY'
import yaml, glob, xml.etree.ElementTree as ET
[yaml.safe_load(open(f)) for f in glob.glob("playbooks/*.yaml")]
ET.fromstring("<root>" + open("wazuh/custom_rules/sentinelforge_rules.xml").read() + "</root>")
print("ok")
PY
```

CI runs all of the above on every push to master and every PR.

---

## Screenshots

Drop PNGs into `docs/screenshots/` and they'll show up here:

- ![Dashboard](docs/screenshots/dashboard.png)
- ![Alert detail with enrichment](docs/screenshots/alert-detail.png)
- ![Case detail with correlated alerts and evidence](docs/screenshots/case-detail.png)
- ![MITRE ATT&CK coverage heatmap](docs/screenshots/mitre.png)
- ![Playbook dry-run](docs/screenshots/playbooks.png)
- ![IOC watchlist](docs/screenshots/iocs.png)
- ![Audit log](docs/screenshots/audit.png)

---

## Roadmap

- Authentication + RBAC (currently all endpoints open — lab use only)
- Prometheus `/metrics` + Grafana for SOC ops health
- Frontend tests (Playwright smoke)
- Webhook + email notifications
- Sigma rule import → Wazuh translation
- Multi-tenant isolation
- HA: clustered indexer, multi-replica backend behind nginx

---

## Team

Built as a college cybersecurity capstone — zero budget, all free /
open-source tooling. Contributors:

- **Farhad** ([@fab561](https://github.com/fab561)) — M1 lead, infra
- **Kunal** ([@kc-2001-sys](https://github.com/kc-2001-sys)) — M2 enrichment
- **Tathagata** ([@TathagataXTron](https://github.com/TathagataXTron)) — M3 playbooks
- **Chandrakant** ([@Chandra721457](https://github.com/Chandra721457)) — M4 frontend
- **Ayush** ([@14DF-3812](https://github.com/14DF-3812)) — M5 honeypot

## License

MIT
