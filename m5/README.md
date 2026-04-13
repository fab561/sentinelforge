# Module 5 — Raspberry Pi Honeypot (Ayush)

## What this does

Runs a **Cowrie SSH honeypot** that attracts attackers and a **Wazuh agent** that ships their activity logs into the SentinelForge pipeline.

```
Attacker → SSH port 2222 → Cowrie (fake shell)
                                ↓ writes cowrie.json
                         Wazuh Agent (reads logs)
                                ↓ ships events
                         Wazuh Manager
                                ↓ indexed
                         M1 Wazuh Poller
                                ↓ normalizes
                         PostgreSQL + Redis → M2 → M3 → M4
```

---

## Run on laptop (development)

```bash
# From repo root
docker compose up -d cowrie wazuh-agent

# Verify Cowrie is listening
docker logs sf-cowrie

# Verify agent registered with manager
docker logs sf-wazuh-agent

# Test: SSH into the honeypot (will be logged as an attack)
ssh root@localhost -p 2222
# Use password: password   (from userdb.txt — honeypot accepts it)
```

---

## Deploy on Raspberry Pi (production)

**Requirements:** RPi 3B+ or newer, Docker installed, same network as SentinelForge stack.

```bash
# 1. Clone repo on RPi
git clone https://github.com/fab561/sentinelforge.git
cd sentinelforge

# 2. Copy .env from main machine (or create new one)
cp .env.example .env
# Edit .env: set WAZUH_MANAGER_IP to your main machine's IP

# 3. Run ONLY the M5 services (rest of stack runs on main machine)
docker compose up -d cowrie wazuh-agent

# 4. Confirm agent appears in Wazuh Dashboard
# → Open http://<main-machine>:5601 → Agents → should see "honeypot-cowrie"
```

---

## What Wazuh rules fire (already configured)

| Rule ID | Event | Level |
|---------|-------|-------|
| 100200 | Any honeypot connection | 12 |
| 100201 | SSH login attempt (fail or success) | 14 |
| 100202 | Attacker ran commands | 15 |
| 100203 | Attacker tried to download file | 15 |

These rules → M1 normalizer → M2 enrichment (VT checks attacker IP) → M3 playbook → M4 shows attack in dashboard.

---

## Files

```
m5/
├── cowrie/
│   ├── cowrie.cfg     # Honeypot config (fake hostname, timeouts, JSON logging)
│   └── userdb.txt     # Credentials the honeypot accepts (weak passwords = bots connect)
└── wazuh-agent/
    ├── Dockerfile     # Ubuntu 22.04 + wazuh-agent (multi-arch: works on RPi ARM64)
    ├── ossec.conf     # Agent config: reads cowrie.json, ships to wazuh-manager
    └── entrypoint.sh  # Waits for manager → registers → starts agent daemons
```

---

## Troubleshooting

**Agent not connecting to manager:**
```bash
docker exec sf-wazuh-agent cat /var/ossec/logs/ossec.log | tail -20
```

**Cowrie not writing logs:**
```bash
docker exec sf-cowrie ls /home/cowrie/cowrie/var/log/cowrie/
```

**Check events reaching M1:**
```bash
# Connect to honeypot (triggers an event)
ssh root@localhost -p 2222   # password: root

# Check DB for the alert
docker exec sf-postgres psql -U sf_admin -d sentinelforge \
  -c "SELECT alert_id, title, category, status FROM alerts ORDER BY created_at DESC LIMIT 5;"
```
