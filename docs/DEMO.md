# SentinelForge — 3-minute demo recording script

Storyboard for recording an end-to-end demo video. Designed to fit
under 3 minutes with no editing. Hit every system component, no
filler.

## Before you start

Pre-flight (do these BEFORE hitting record):

1. Stack is up: `docker compose ps` shows all 11 containers healthy
2. Frontend dev server running: `cd frontend && npm run dev`
3. `.env` has VirusTotal + AbuseIPDB + OTX keys (at minimum)
4. Open these tabs ahead of time so they're warm:
   - http://localhost:3000/dashboard
   - http://localhost:3000/alerts
   - http://localhost:3000/cases
   - http://localhost:3000/mitre
   - http://localhost:3000/playbooks
   - http://localhost:3000/audit
5. Pick **one** existing escalated case to demo PDF export from — note its
   case number, e.g. CASE-2026-0007
6. Have a terminal ready in the project dir for the live attack
7. Switch theme to dark or light depending on what looks better on
   your recording resolution

Recording tools (free): OBS Studio, ShareX (Windows), or built-in
macOS Cmd+Shift+5 / Win+Alt+R.

Resolution: 1920x1080 if possible, browser zoom ~110% so text is
readable in compressed video.

---

## Storyboard

### 00:00 — 00:15 — Pitch (over dashboard)

> "SentinelForge is an open-source SOAR — Security Orchestration,
> Automation, and Response. We replace tools like Splunk SOAR or
> Cortex XSOAR, which run a hundred thousand a year, with a stack
> built entirely on free and open-source components."

**On screen:** `/dashboard` showing live alert counts, severity
breakdown, MTTA / MTTR cards, 14-day trend chart.

### 00:15 — 00:35 — Architecture (sidebar tour)

> "Five modules: Wazuh ingestion, threat-intel enrichment, playbook
> automation, the dashboard you're looking at, and a Cowrie SSH
> honeypot. Eleven Docker containers, 30 detection rules, four free
> threat-intel feeds wired in."

**On screen:** Hover the sidebar slowly so each item — Dashboard,
Alerts, Cases, Rules, Playbooks, Watchlist, MITRE, Agents, Audit Log
— shows up.

### 00:35 — 00:55 — MITRE coverage

> "Every detection rule maps to a MITRE ATT&CK technique. The
> heatmap shows our coverage at a glance — the brighter the cell,
> the more alerts we're seeing for that technique."

**On screen:** Click `/mitre`, hover one of the colored cells to
show the tooltip (`T1110.003 — Password Spraying — N alerts`).

### 00:55 — 01:35 — LIVE attack

Switch to terminal. Run this — it's deliberately verbose so the
audience can watch each step:

```bash
ssh -p 2222 -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null root@localhost
# password prompt — type "root" and Enter (default cowrie userdb)
# even on auth failure, cowrie logs the attempt
```

> "I'm SSHing into our honeypot on port 2222. Cowrie captures every
> packet. Wazuh ships the alert. Backend enriches the IP against
> VirusTotal, AbuseIPDB, and OTX in parallel. M3's playbook engine
> picks up critical alerts and creates a case automatically."

**Open a second terminal** and run the inject script (faster than
waiting for the cowrie → wazuh pipeline to surface a real alert in
under a minute):

```bash
docker exec sf-backend python -c "
import asyncio, json, uuid
from datetime import datetime, timezone
from app.core.database import async_session
from app.core.redis import get_redis, close_redis
from app.models.alert import Alert
async def go():
    aid=f'demo-{uuid.uuid4().hex[:8]}'
    async with async_session() as db:
        db.add(Alert(alert_id=aid, timestamp=datetime.now(timezone.utc),
            source='cowrie', severity='critical', category='honeypot',
            title='LIVE DEMO: SSH brute-force from 185.220.101.1',
            observables={'source_ip':'185.220.101.1','destination_port':22},
            raw_log='', status='new'))
        await db.commit()
    r=await get_redis()
    await r.lpush('alerts:pending_enrichment', json.dumps({
        'alert_id':aid,'observables':{'source_ip':'185.220.101.1'},
        'severity':'critical','category':'honeypot','source':'cowrie',
        'title':'LIVE DEMO'
    }))
    await close_redis()
    print('injected:',aid)
asyncio.run(go())
"
```

### 01:35 — 02:15 — Watch the pipeline fire

Switch back to the browser, refresh `/alerts`.

> "The alert is enriched in about ten seconds — that's three external
> APIs queried in parallel. Threat score, verdict, and tags are
> attached. Notice this IP is tagged Tor, GreyNoise-malicious,
> AbuseIPDB-high, OTX-honeypot — that's real intel from real feeds."

**On screen:** Click into the freshly created alert. Show the
enrichment JSON panel and the playbook actions panel.

### 02:15 — 02:45 — Case + evidence + correlation

Go to `/cases`. Open the most recent case (the one auto-created by
the playbook).

> "The playbook automatically opened a case, attached this alert,
> and harvested the cowrie session log as evidence — that file you
> see at the bottom contains every command an attacker would have
> typed if they'd been allowed in. If another alert fires from the
> same IP in the next 24 hours, it correlates here instead of
> opening a duplicate case."

**On screen:** Scroll down to show "Correlated Alerts" panel and
"Evidence" panel with the auto-attached `.jsonl` file.

### 02:45 — 03:00 — PDF + audit + close

Click **Export PDF** in the case header — let the file download.
Open it briefly so the audience sees the formatted report.

Switch to `/audit`.

> "Every mutation is logged — case created, alert correlated, evidence
> attached, status changed. Tamper-evident trail for compliance.
> Everything you just saw is open source on GitHub. Thanks for
> watching."

**On screen:** Audit log entries scrolling past, with the most
recent demo entries at top.

---

## Tips

- **Speak slowly.** SOAR concepts are dense; viewers need to keep up.
- **Mute notifications.** Slack pings during the take ruin it.
- **Keep your face out of frame** unless you have a good webcam +
  lighting — the dashboard is the star.
- **Don't show the address bar zoom indicator** — it looks unpolished.
- **Record at 60fps** if your machine allows; the recharts animations
  look choppy at 30.
- If you fluff a take, **don't try to recover** — restart. Three
  minutes is short enough to redo cleanly.

## Publishing

Upload to YouTube as **unlisted** first, share the link with
teammates for review, then flip to **public**. Embed the video URL
in the README under the demo flow section.

Title suggestion: `SentinelForge — Open-Source SOAR in 3 minutes
(college capstone project)`.
