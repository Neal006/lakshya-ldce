import httpx
from app.config import BREVO_API_KEY


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


async def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    text_content: str = None,
) -> bool:
    if not BREVO_API_KEY:
        return False

    payload = {
        "sender": {
            "name": "TS-14 Complaint Resolution",
            "email": "support@ts14.com",
        },
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content,
    }

    if text_content:
        payload["textContent"] = text_content

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                BREVO_API_URL,
                json=payload,
                headers={
                    "api-key": BREVO_API_KEY,
                    "Content-Type": "application/json",
                },
            )
            return response.status_code in (200, 201)
    except (httpx.HTTPError, httpx.TimeoutException):
        return False


async def send_resolution_notification(
    customer_name: str,
    customer_email: str,
    complaint_id: str,
    category: str,
    resolution_steps: list,
) -> bool:
    steps_html = "".join(f"<li>{step}</li>" for step in resolution_steps)
    steps_text = "\n".join(f"  {step}" for step in resolution_steps)

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1a1a1a;">Your Complaint Has Been Updated</h2>
        <p>Dear {customer_name},</p>
        <p>Your complaint <strong>#{complaint_id}</strong> has been processed.</p>
        <h3 style="color: #4a4a4a;">Category: {category}</h3>
        <h3 style="color: #4a4a4a;">Resolution Steps:</h3>
        <ol style="line-height: 1.8;">{steps_html}</ol>
        <p style="margin-top: 20px; padding: 12px; background: #f0f4ff; border-radius: 6px;">
            <strong>Complaint ID:</strong> {complaint_id}
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #888; font-size: 12px;">
            TS-14 Complaint Resolution Engine &mdash; This is an automated message.
        </p>
    </div>
    """

    text = f"""
Your complaint has been processed.

Complaint ID: {complaint_id}
Category: {category}

Resolution Steps:
{steps_text}

If you need further assistance, please contact our support team.

-- TS-14 Complaint Resolution Engine
    """

    return await send_email(
        to_email=customer_email,
        to_name=customer_name,
        subject=f"Complaint Update #{complaint_id} - {category}",
        html_content=html,
        text_content=text.strip(),
    )


async def send_escalation_notification(
    customer_name: str,
    customer_email: str,
    complaint_id: str,
    reason: str,
) -> bool:
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #dc2626;">Your Complaint Has Been Escalated</h2>
        <p>Dear {customer_name},</p>
        <p>Your complaint <strong>#{complaint_id}</strong> has been escalated to senior management.</p>
        <p style="padding: 12px; background: #fef2f2; border-left: 4px solid #dc2626; border-radius: 4px;">
            <strong>Reason:</strong> {reason}
        </p>
        <p>Our team is reviewing your case with priority. You will receive an update shortly.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #888; font-size: 12px;">
            TS-14 Complaint Resolution Engine &mdash; This is an automated message.
        </p>
    </div>
    """

    text = f"""
Your complaint has been escalated.

Complaint ID: {complaint_id}
Reason: {reason}

Our team is reviewing your case with priority.

-- TS-14 Complaint Resolution Engine
    """

    return await send_email(
        to_email=customer_email,
        to_name=customer_name,
        subject=f"Escalation Notice #{complaint_id}",
        html_content=html,
        text_content=text.strip(),
    )


async def send_sla_breach_notification(
    customer_name: str,
    customer_email: str,
    complaint_id: str,
    sla_deadline: str,
) -> bool:
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #dc2626;">SLA Breach Notice</h2>
        <p>Dear {customer_name},</p>
        <p>We regret to inform you that the resolution of your complaint <strong>#{complaint_id}</strong> has exceeded our service level agreement deadline.</p>
        <p style="padding: 12px; background: #fef2f2; border-left: 4px solid #dc2626; border-radius: 4px;">
            <strong>SLA Deadline was:</strong> {sla_deadline}
        </p>
        <p>Our team is working to resolve this as quickly as possible. We apologize for the inconvenience.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #888; font-size: 12px;">
            TS-14 Complaint Resolution Engine &mdash; This is an automated message.
        </p>
    </div>
    """

    text = f"""
SLA Breach Notice

Complaint ID: {complaint_id}
SLA Deadline: {sla_deadline}

We apologize for the delay. Our team is working to resolve this quickly.

-- TS-14 Complaint Resolution Engine
    """

    return await send_email(
        to_email=customer_email,
        to_name=customer_name,
        subject=f"SLA Breach Notice #{complaint_id}",
        html_content=html,
        text_content=text.strip(),
    )