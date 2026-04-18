"""
email_html.py — Branded HTML email builder for solv.ai (black + orange theme).

build_solvai_reply_html_from_resolution()
    Returns Gmail-paste-ready HTML (just the email table, no <html>/<head>/<body>).
    → Open the saved .html file in a browser, Ctrl+A, Ctrl+C, paste into Gmail compose.
    → Or drop the `html` string from the API response into Gmail via browser console:
          document.querySelector('[aria-label="Message Body"]').innerHTML = '<paste here>'

write_reply_html_file()
    Wraps the paste-ready HTML in a full document so you can preview it in a browser.
"""

from __future__ import annotations

import html
import re
from pathlib import Path


def _paragraphs(body_text: str) -> list[str]:
    raw = (body_text or "").strip().split("\n\n")
    return [p.strip() for p in raw if p.strip()]


def _excerpt(text: str, max_len: int = 600) -> str:
    t = (text or "").strip()
    return t if len(t) <= max_len else t[: max_len - 3] + "..."


def build_solvai_reply_html_from_resolution(
    *,
    subject: str,
    customer_name: str,
    complaint_id: int | str,
    category: str,
    priority: str,
    status: str,
    original_text: str,
    customer_response: str,
    resolution_steps: list[str],
    follow_up_timeline: str,
    estimated_resolution_time: str,
    assigned_team: str,
    escalation_required: bool,
    sla_deadline_hours: int,
) -> str:
    """
    Returns Gmail-paste-ready HTML — a self-contained <table> with full inline styles.
    No <html>/<head>/<body> wrapper so it slots directly into Gmail's compose body.

    HOW TO PASTE INTO GMAIL
    ──────────────────────
    Option A (easiest — no extensions needed):
      1. Open the saved .html file in Chrome/Edge.
      2. Ctrl+A  →  Ctrl+C
      3. Open Gmail compose  →  Ctrl+V
         (Switch to "Plain text" mode first if Gmail ignores formatting, then switch back.)

    Option B (console — paste the `html` field from the API response):
      1. Open Gmail compose in Chrome.
      2. Click inside the message body.
      3. Open DevTools console (F12) and run:
            document.querySelector('[aria-label="Message Body"]').innerHTML = `<PASTE_HTML_HERE>`;
    """

    safe = lambda s: html.escape(str(s or ""), quote=True)

    s_subject  = safe(subject.strip() or "Update from solv.ai")
    s_name     = safe(customer_name.strip() or "Valued Customer")
    s_cid      = safe(complaint_id)
    s_cat      = safe(category)
    s_pri      = safe(priority)
    s_stat     = safe(status)
    s_follow   = safe(follow_up_timeline)
    s_eta      = safe(estimated_resolution_time)
    s_team     = safe(assigned_team)
    s_sla      = safe(sla_deadline_hours)

    # ── Greeting + body paragraphs ────────────────────────────────────
    body_blocks = "".join(
        f'<p style="margin:0 0 14px 0;color:#1a1a1a;font-size:15px;'
        f'line-height:1.65;font-family:Arial,sans-serif;">{safe(p)}</p>'
        for p in _paragraphs(customer_response)
    )

    # ── Original complaint quote ──────────────────────────────────────
    orig = _excerpt(original_text)
    query_block = ""
    if orig:
        query_block = (
            '<table role="presentation" cellspacing="0" cellpadding="0" width="100%"'
            ' style="margin:18px 0;">'
            '<tr><td style="border-left:3px solid #ff7a18;padding:10px 14px;'
            'background:#fff8f3;border-radius:0 6px 6px 0;">'
            '<p style="margin:0 0 6px 0;color:#cc5500;font-size:11px;'
            'letter-spacing:0.08em;text-transform:uppercase;font-family:Arial,sans-serif;">'
            'Your message</p>'
            f'<p style="margin:0;color:#555555;font-size:13px;line-height:1.55;'
            f'font-style:italic;font-family:Arial,sans-serif;">{safe(orig)}</p>'
            '</td></tr></table>'
        )

    # ── Resolution steps ──────────────────────────────────────────────
    steps_section = ""
    step_items = "".join(
        f'<li style="margin:0 0 7px 0;color:#333333;font-size:13px;'
        f'line-height:1.55;font-family:Arial,sans-serif;">{safe(s.strip())}</li>'
        for s in (resolution_steps or []) if s.strip()
    )
    if step_items:
        steps_section = (
            '<table role="presentation" cellspacing="0" cellpadding="0" width="100%"'
            ' style="margin:22px 0 0 0;">'
            '<tr><td style="padding:16px 18px;background:#fff8f3;'
            'border:1px solid #ffd4aa;border-radius:8px;">'
            '<p style="margin:0 0 10px 0;color:#cc5500;font-size:11px;'
            'text-transform:uppercase;letter-spacing:0.1em;font-family:Arial,sans-serif;">'
            "What we&rsquo;re doing next</p>"
            f'<ul style="margin:0;padding-left:18px;">{step_items}</ul>'
            '</td></tr></table>'
        )

    # ── Escalation notice ─────────────────────────────────────────────
    esc_note = ""
    if escalation_required:
        esc_note = (
            '<p style="margin:14px 0 0 0;padding:10px 14px;background:#fff3e0;'
            'border:1px solid #ffb74d;border-radius:6px;color:#e65100;'
            'font-size:13px;line-height:1.5;font-family:Arial,sans-serif;">'
            "This matter has been <strong>escalated</strong> to a specialist team for priority handling."
            "</p>"
        )

    # ── Timeline table ────────────────────────────────────────────────
    def _row(label: str, value: str) -> str:
        return (
            f'<tr>'
            f'<td style="padding:5px 0;color:#888888;font-size:13px;'
            f'font-family:Arial,sans-serif;width:50%;">{label}</td>'
            f'<td style="padding:5px 0;color:#1a1a1a;font-size:13px;'
            f'font-family:Arial,sans-serif;text-align:right;">{value}</td>'
            f'</tr>'
        )

    timeline_block = (
        '<table role="presentation" cellspacing="0" cellpadding="0" width="100%"'
        ' style="margin:22px 0 0 0;border-top:1px solid #e0e0e0;padding-top:18px;">'
        '<tr><td colspan="2" style="padding:0 0 10px 0;color:#888888;font-size:11px;'
        'text-transform:uppercase;letter-spacing:0.08em;font-family:Arial,sans-serif;">'
        'Timeline</td></tr>'
        + _row("Follow-up", s_follow)
        + _row("Est. resolution", s_eta)
        + _row("Primary team", s_team)
        + _row("SLA target", f"{s_sla} hours")
        + "</table>"
    )

    # ── Assemble full paste-ready table ──────────────────────────────
    return f"""<table role="presentation" cellspacing="0" cellpadding="0"
  style="width:100%;max-width:600px;font-family:Arial,sans-serif;border:1px solid #e0e0e0;border-radius:10px;overflow:hidden;">

  <!-- Header -->
  <tr>
    <td style="padding:24px 28px 10px 28px;background:#1a1a1a;border-bottom:2px solid #ff7a18;">
      <p style="margin:0;font-size:21px;font-weight:700;letter-spacing:-0.02em;font-family:Arial,sans-serif;">
        <span style="color:#ffffff;">solv</span><span style="color:#ff7a18;">.ai</span>
      </p>
      <p style="margin:6px 0 0 0;color:#aaaaaa;font-size:12px;font-family:Arial,sans-serif;">Customer reply</p>
    </td>
  </tr>

  <!-- Ref line -->
  <tr>
    <td style="padding:14px 28px 0 28px;background:#ffffff;">
      <p style="margin:0;color:#888888;font-size:12px;font-family:Arial,sans-serif;">
        Ref <span style="color:#ff7a18;">#{s_cid}</span>
        &nbsp;&middot;&nbsp; {s_cat}
        &nbsp;&middot;&nbsp; {s_pri}
        &nbsp;&middot;&nbsp; {s_stat}
      </p>
    </td>
  </tr>

  <!-- Subject -->
  <tr>
    <td style="padding:14px 28px 6px 28px;background:#ffffff;">
      <p style="margin:0 0 4px 0;color:#cc5500;font-size:11px;text-transform:uppercase;
         letter-spacing:0.12em;font-family:Arial,sans-serif;">Subject</p>
      <h1 style="margin:0;color:#1a1a1a;font-size:19px;font-weight:600;
          line-height:1.35;font-family:Arial,sans-serif;">{s_subject}</h1>
    </td>
  </tr>

  <!-- Body -->
  <tr>
    <td style="padding:16px 28px 28px 28px;background:#ffffff;">
      <p style="margin:0 0 16px 0;color:#1a1a1a;font-size:15px;
         line-height:1.65;font-family:Arial,sans-serif;">Hi {s_name},</p>
      {query_block}
      {body_blocks}
      {steps_section}
      {esc_note}
      {timeline_block}
      <p style="margin:24px 0 4px 0;color:#1a1a1a;font-size:15px;
         font-family:Arial,sans-serif;">Warm regards,</p>
      <p style="margin:0;color:#ff7a18;font-size:15px;font-weight:600;
         font-family:Arial,sans-serif;">Tanya</p>
      <p style="margin:3px 0 0 0;color:#888888;font-size:13px;
         font-family:Arial,sans-serif;">solv.ai</p>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="padding:14px 28px;background:#f5f5f5;border-top:1px solid #e0e0e0;">
      <p style="margin:0;color:#aaaaaa;font-size:11px;line-height:1.5;
         text-align:center;font-family:Arial,sans-serif;">
        solv.ai &mdash; automated customer resolution platform
      </p>
    </td>
  </tr>

</table>"""


def write_reply_html_file(directory: Path, filename_stem: str, html_document: str) -> Path:
    """Wrap the paste-ready table in a full HTML document and save for browser preview."""
    directory.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^\w\-]+", "_", filename_stem).strip("_") or "reply"
    path = directory / f"{safe_stem}.html"

    full_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>solv.ai reply preview</title>
  <style>
    body {{ margin: 0; padding: 32px 16px; background: #f0f0f0; }}
    /* Gmail paste instructions banner */
    .instructions {{
      max-width: 600px; margin: 0 auto 18px auto;
      background: #fffbe6; border: 1px solid #ffe58f; border-radius: 8px;
      padding: 12px 16px; font-family: Arial, sans-serif; font-size: 13px; color: #555;
    }}
    .instructions strong {{ color: #cc5500; }}
  </style>
</head>
<body>
  <div class="instructions">
    <strong>How to paste into Gmail:</strong>
    Press <strong>Ctrl+A</strong> on this page, then <strong>Ctrl+C</strong>,
    open Gmail compose and press <strong>Ctrl+V</strong>.
  </div>
  {html_document}
</body>
</html>"""

    path.write_text(full_doc, encoding="utf-8")
    return path.resolve()
