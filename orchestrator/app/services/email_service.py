"""
email_service.py — SMTP email notification service for SentinelAI.

All email calls are wrapped in try/except. Email failures NEVER crash the pipeline.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..core.config import settings


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an HTML email notification. Returns True on success, False on failure.

    This function is intentionally fault-tolerant — if SMTP credentials are
    missing, the recipient is empty, or the server is unreachable, it will
    print a warning and return False without raising.
    """
    if not to_email or not to_email.strip():
        print("    [📧] Skipped: no email address provided.")
        return False

    sender = settings.SMTP_EMAIL
    password = settings.SMTP_PASSWORD

    if not sender or not password:
        print("    [📧] Skipped: SMTP credentials not configured in .env")
        return False

    html_body = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0f172a; color: #e2e8f0; border-radius: 12px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #6366f1, #8b5cf6); padding: 24px 32px;">
            <h1 style="margin: 0; font-size: 22px; color: white;">🛡️ SentinelAI</h1>
            <p style="margin: 4px 0 0; font-size: 13px; color: rgba(255,255,255,0.8);">Autonomous Security Pipeline</p>
        </div>
        <div style="padding: 28px 32px;">
            <h2 style="margin: 0 0 16px; font-size: 18px; color: #f1f5f9;">{subject}</h2>
            <div style="font-size: 14px; line-height: 1.7; color: #cbd5e1;">
                {body}
            </div>
        </div>
        <div style="padding: 16px 32px; background: #1e293b; font-size: 11px; color: #64748b; text-align: center;">
            Powered by SentinelAI — Autonomous Purple Team Security
        </div>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[SentinelAI] {subject}"
    msg["From"] = sender
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(sender, password)
            server.send_message(msg)
        print(f"    [📧] Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"    [📧] Email failed (non-blocking): {e}")
        return False


# ── Pre-built notification templates ──────────────────────────────

def notify_scan_started(to_email: str, repo_url: str) -> bool:
    """Send 'scan started' notification."""
    return send_email(
        to_email,
        "Scan Started",
        f"We have started analyzing your repository.<br><br>"
        f"<strong>Repository:</strong> <code>{repo_url}</code><br><br>"
        f"You will receive another email when the results are ready."
    )


def notify_detection_complete(to_email: str, repo_url: str, vuln_count: int) -> bool:
    """Send 'detection-only scan complete' notification."""
    return send_email(
        to_email,
        "Scan Completed",
        f"Repository scan is complete.<br><br>"
        f"<strong>Repository:</strong> <code>{repo_url}</code><br>"
        f"<strong>Vulnerabilities Found:</strong> {vuln_count}<br><br>"
        f"Visit the SentinelAI dashboard to view the full report."
    )


def notify_fix_in_progress(to_email: str, repo_url: str, cve_id: str) -> bool:
    """Send 'fix in progress' notification."""
    return send_email(
        to_email,
        "Fix In Progress",
        f"We detected a vulnerability and are working on a fix.<br><br>"
        f"<strong>Repository:</strong> <code>{repo_url}</code><br>"
        f"<strong>Vulnerability:</strong> <code>{cve_id}</code><br><br>"
        f"You will receive another email when the patch is ready."
    )


def notify_patch_complete(to_email: str, repo_url: str, cve_id: str, pr_url: str = None) -> bool:
    """Send 'patch completed' notification with optional PR link."""
    pr_section = ""
    if pr_url:
        pr_section = (
            f"<br><strong>Pull Request:</strong> "
            f"<a href='{pr_url}' style='color: #818cf8;'>{pr_url}</a>"
        )

    return send_email(
        to_email,
        "Patch Completed",
        f"A security patch has been generated and validated.<br><br>"
        f"<strong>Repository:</strong> <code>{repo_url}</code><br>"
        f"<strong>Vulnerability Fixed:</strong> <code>{cve_id}</code>"
        f"{pr_section}<br><br>"
        f"The patch was tested against an AI-generated exploit in a sandbox and <strong>passed</strong>."
    )


def notify_pipeline_failed(to_email: str, repo_url: str, error: str) -> bool:
    """Send 'pipeline failed' notification."""
    return send_email(
        to_email,
        "Scan Failed",
        f"We encountered an error while processing your repository.<br><br>"
        f"<strong>Repository:</strong> <code>{repo_url}</code><br>"
        f"<strong>Error:</strong> {error}<br><br>"
        f"Please check the SentinelAI dashboard for details."
    )
