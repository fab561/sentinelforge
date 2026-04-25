"""Case PDF export.

Renders a forensic-style case report: header, lifecycle timestamps,
correlated alerts, evidence inventory, and recent audit trail. The
output is a self-contained PDF an analyst can attach to an email or
upload to a ticketing system without losing context.

fpdf2 is sync-only; we run it in asyncio.to_thread so the endpoint
stays non-blocking.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from io import BytesIO
from typing import Any

from fpdf import FPDF


def _fmt_dt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S UTC")
    return str(value)


def _safe(text: Any) -> str:
    """fpdf2 with the default core font only handles latin-1; strip the rest
    so a stray emoji or unicode tag in an alert title can't 500 the export."""
    if text is None:
        return ""
    s = str(text)
    return s.encode("latin-1", "replace").decode("latin-1")


class _CaseReport(FPDF):
    def __init__(self, case_number: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self._case_number = case_number
        self.set_auto_page_break(auto=True, margin=18)

    def header(self) -> None:
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, _safe(f"SentinelForge — Case Report — {self._case_number}"), border=0)
        self.ln(10)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, f"Page {self.page_no()}", align="C")

    def heading(self, text: str) -> None:
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(20, 20, 20)
        self.set_fill_color(230, 240, 250)
        self.cell(0, 7, _safe(text), border=0, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def kv_row(self, label: str, value: Any) -> None:
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(80, 80, 80)
        self.cell(40, 5, _safe(label))
        self.set_font("Helvetica", "", 9)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 5, _safe(value), new_x="LMARGIN", new_y="NEXT")


def _render_pdf_sync(
    case: dict,
    alerts: list[dict],
    evidence: list[dict],
    audit: list[dict],
) -> bytes:
    pdf = _CaseReport(case_number=case.get("case_number", "?"))
    pdf.add_page()

    # ── Header block ─────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 9, _safe(case.get("title", "Untitled")), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, _safe(
        f"Status: {case.get('status', '?').upper()}   "
        f"Severity: {(case.get('severity') or '—').upper()}"
    ), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Lifecycle ───────────────────────────────────────────────
    pdf.heading("Case Lifecycle")
    pdf.kv_row("Case Number", case.get("case_number"))
    pdf.kv_row("Created", _fmt_dt(case.get("created_at")))
    pdf.kv_row("Acknowledged", _fmt_dt(case.get("acknowledged_at")))
    pdf.kv_row("Resolved", _fmt_dt(case.get("resolved_at")))
    pdf.kv_row("Closed", _fmt_dt(case.get("closed_at")))
    if case.get("description"):
        pdf.ln(1)
        pdf.kv_row("Description", case["description"])
    pdf.ln(3)

    # ── Correlated alerts ───────────────────────────────────────
    pdf.heading(f"Correlated Alerts ({len(alerts)})")
    if not alerts:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 5, "No alerts attached.", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(35, 5, "Time",     border=1, fill=True)
        pdf.cell(20, 5, "Severity", border=1, fill=True)
        pdf.cell(20, 5, "Verdict",  border=1, fill=True)
        pdf.cell(15, 5, "Score",    border=1, fill=True, align="R")
        pdf.cell(0,  5, "Title",    border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        for a in alerts:
            pdf.cell(35, 5, _safe(_fmt_dt(a.get("timestamp"))[:19]), border=1)
            pdf.cell(20, 5, _safe((a.get("severity") or "—").upper()), border=1)
            pdf.cell(20, 5, _safe((a.get("verdict") or "—").upper()), border=1)
            pdf.cell(15, 5, _safe(a.get("threat_score") or "—"), border=1, align="R")
            pdf.cell(0,  5, _safe((a.get("title") or "")[:60]), border=1,
                     new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ── Evidence ────────────────────────────────────────────────
    pdf.heading(f"Evidence ({len(evidence)})")
    if not evidence:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 5, "No evidence attached.", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(70, 5, "Filename", border=1, fill=True)
        pdf.cell(30, 5, "Kind",     border=1, fill=True)
        pdf.cell(25, 5, "Size",     border=1, fill=True, align="R")
        pdf.cell(0,  5, "SHA-256",  border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        for e in evidence:
            pdf.cell(70, 5, _safe((e.get("filename") or "")[:40]), border=1)
            pdf.cell(30, 5, _safe(e.get("kind", "—")), border=1)
            pdf.cell(25, 5, _safe(e.get("size_bytes", 0)), border=1, align="R")
            pdf.cell(0,  5, _safe((e.get("sha256") or "")[:32] + "..."),
                     border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ── Audit trail (last 20) ───────────────────────────────────
    recent = audit[:20]
    pdf.heading(f"Audit Trail ({len(recent)} most recent)")
    if not recent:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 5, "No audit entries.", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "", 8)
        for r in recent:
            ts = _fmt_dt(r.get("created_at"))[:19]
            pdf.set_text_color(120, 120, 120)
            pdf.cell(35, 5, _safe(ts))
            pdf.set_text_color(20, 20, 20)
            pdf.cell(0, 5, _safe(r.get("action", "")), new_x="LMARGIN", new_y="NEXT")

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


async def render_case_pdf(
    case: dict,
    alerts: list[dict],
    evidence: list[dict],
    audit: list[dict],
) -> bytes:
    return await asyncio.to_thread(_render_pdf_sync, case, alerts, evidence, audit)
