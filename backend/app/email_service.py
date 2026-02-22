import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def is_email_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send an email notification. Returns True on success."""
    if not is_email_configured():
        logger.warning("Email not configured, skipping send")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        if settings.smtp_use_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)

        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(msg["From"], to, msg.as_string())
        server.quit()
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


def build_new_listing_email(properties: list[dict]) -> str:
    """Build HTML email for new listing notifications."""
    rows = ""
    for p in properties:
        price_str = f"{p['price']:,.0f} CZK" if p.get('price') else "Cena na dotaz"
        rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #eee;">
                <a href="{p.get('url', '#')}" style="color: #2563eb; font-weight: 600; text-decoration: none;">{p.get('title', 'Nemovitost')}</a>
                <br/><span style="color: #666; font-size: 13px;">{p.get('city', '')} | {p.get('disposition', '')} | {p.get('size_m2', '')} m²</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right; font-weight: 700; color: #2563eb;">
                {price_str}
            </td>
        </tr>
        """

    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1e3a8a; margin-bottom: 16px;">Nove nemovitosti</h2>
        <p style="color: #666; margin-bottom: 20px;">Nalezli jsme {len(properties)} novych nemovitosti odpovidajicich vasim filtrum.</p>
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #eee; border-radius: 8px;">
            <thead>
                <tr style="background: #f8fafc;">
                    <th style="padding: 10px 12px; text-align: left; font-size: 13px; color: #666;">Nemovitost</th>
                    <th style="padding: 10px 12px; text-align: right; font-size: 13px; color: #666;">Cena</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">Czech Real Estate Tracker</p>
    </div>
    """


def build_price_drop_email(properties: list[dict]) -> str:
    """Build HTML email for price drop notifications."""
    rows = ""
    for p in properties:
        old_price = f"{p['old_price']:,.0f}" if p.get('old_price') else "?"
        new_price = f"{p['new_price']:,.0f}" if p.get('new_price') else "?"
        rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #eee;">
                <a href="{p.get('url', '#')}" style="color: #2563eb; font-weight: 600; text-decoration: none;">{p.get('title', 'Nemovitost')}</a>
                <br/><span style="color: #666; font-size: 13px;">{p.get('city', '')} | {p.get('disposition', '')}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">
                <span style="text-decoration: line-through; color: #999;">{old_price} CZK</span>
                <br/><span style="font-weight: 700; color: #16a34a;">{new_price} CZK</span>
            </td>
        </tr>
        """

    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #16a34a; margin-bottom: 16px;">Pokles cen</h2>
        <p style="color: #666; margin-bottom: 20px;">U {len(properties)} nemovitosti doslo ke snizeni ceny.</p>
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #eee; border-radius: 8px;">
            <thead>
                <tr style="background: #f8fafc;">
                    <th style="padding: 10px 12px; text-align: left; font-size: 13px; color: #666;">Nemovitost</th>
                    <th style="padding: 10px 12px; text-align: right; font-size: 13px; color: #666;">Cena</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">Czech Real Estate Tracker</p>
    </div>
    """
