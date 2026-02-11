import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import settings

logger = logging.getLogger(__name__)


def _build_alert_summary_html(alerts: list[dict]) -> str:
    """Build an HTML email body summarizing new alerts."""
    rows = ""
    for a in alerts:
        alert_type_labels = {
            "status_change": "Statusänderung",
            "committee_scheduled": "Kommission",
            "debate_scheduled": "Debatte",
            "new_document": "Dokument",
            "vote_result": "Abstimmung",
        }
        type_label = alert_type_labels.get(a["alert_type"], a["alert_type"])
        event_date = ""
        if a.get("event_date"):
            try:
                event_date = a["event_date"].strftime("%d.%m.%Y")
            except (AttributeError, ValueError):
                event_date = str(a["event_date"])

        rows += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; font-family: monospace;">{a['business_number']}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{a.get('business_title', '')}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{type_label}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{a['message']}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{event_date}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #333; max-width: 800px; margin: 0 auto;">
        <div style="background: #D52B1E; color: white; padding: 16px 24px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Parlamentsmonitor – Neue Alerts</h2>
        </div>
        <div style="padding: 24px; background: #fff; border: 1px solid #eee; border-top: none; border-radius: 0 0 8px 8px;">
            <p>Sie haben <strong>{len(alerts)}</strong> neue Alert(s):</p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <thead>
                    <tr style="background: #f8f8f8;">
                        <th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #ddd;">Nr.</th>
                        <th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #ddd;">Titel</th>
                        <th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #ddd;">Typ</th>
                        <th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #ddd;">Nachricht</th>
                        <th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #ddd;">Termin</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <p style="color: #888; font-size: 13px; margin-top: 24px;">
                Diese E-Mail wurde automatisch vom Parlamentsmonitor gesendet.
                Sie können die E-Mail-Benachrichtigungen in den Einstellungen deaktivieren.
            </p>
        </div>
    </body>
    </html>
    """


def send_alert_email(to_email: str, to_name: str, alerts: list[dict]) -> bool:
    """Send an alert summary email to a user.

    Returns True on success, False on failure.
    """
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured – skipping email to %s", to_email)
        return False

    if not alerts:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Parlamentsmonitor: {len(alerts)} neue Alert(s)"
    msg["From"] = settings.SMTP_FROM or f"noreply@{settings.SMTP_HOST}"
    msg["To"] = to_email

    # Plain text fallback
    lines = [f"Parlamentsmonitor – {len(alerts)} neue Alert(s)\n"]
    for a in alerts:
        lines.append(f"- {a['business_number']}: {a['message']}")
    text_body = "\n".join(lines)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))

    # HTML version
    html_body = _build_alert_summary_html(alerts)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if settings.SMTP_USE_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
        elif settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)

        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        server.sendmail(msg["From"], [to_email], msg.as_string())
        server.quit()
        logger.info("Alert email sent to %s (%d alerts)", to_email, len(alerts))
        return True
    except Exception:
        logger.exception("Failed to send alert email to %s", to_email)
        return False
