"""Re-runnable rule-catalog seeder.

`seed.py` short-circuits when alerts exist, which is correct for a fresh
initial-data bootstrap but wrong for evolving the rule catalog. This
script upserts SAMPLE_RULES by `name` so adding/editing rules in seed.py
and re-running here keeps the live DB in sync without touching anything
else.

Usage (from backend container):
    docker exec sf-backend python seed_rules.py
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import async_session
from app.models.rule import Rule
from app.models.user import User
from seed import SAMPLE_RULES


async def upsert_rules() -> None:
    async with async_session() as db:
        admin = (
            await db.execute(select(User).where(User.username == "admin"))
        ).scalar_one_or_none()
        if not admin:
            print("No admin user found — run seed.py first.")
            return
        existing = {
            r.name: r
            for r in (await db.execute(select(Rule))).scalars().all()
        }

        created = updated = 0
        for data in SAMPLE_RULES:
            row = existing.get(data["name"])
            if row is None:
                db.add(Rule(**data, created_by=admin.id))
                created += 1
            else:
                row.description = data["description"]
                row.rule_type = data["rule_type"]
                row.definition = data["definition"]
                row.severity = data["severity"]
                row.enabled = data["enabled"]
                row.mitre_techniques = data["mitre_techniques"]
                updated += 1

        await db.commit()
        print(f"Rules synced: {created} created, {updated} updated, {len(SAMPLE_RULES)} total")


if __name__ == "__main__":
    asyncio.run(upsert_rules())
