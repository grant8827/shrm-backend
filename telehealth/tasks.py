from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger("theracare.audit")


@shared_task
def send_emergency_session_email(
    patient_name, therapist_name, recipient_email, session_url, room_id, session_id
):
    """
    Send emergency session email asynchronously via Celery.
    """
    try:
        print(f"[CELERY] Sending emergency email to {recipient_email}")

        email_context = {
            "patient_name": patient_name,
            "therapist_name": therapist_name,
            "session_url": session_url,
            "room_id": room_id,
        }

        email_body = render_to_string("emails/emergency_session.html", email_context)

        result = send_mail(
            subject="Emergency Telehealth Session - Join Now",
            message=f"You have an emergency telehealth session. Join here: {session_url}",
            html_message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )

        logger.info(
            "Emergency session email sent successfully via Celery",
            extra={
                "event_type": "emergency_session_email_sent",
                "session_id": str(session_id),
                "patient_email": recipient_email,
                "email_result": result,
                "timestamp": timezone.now().isoformat(),
            },
        )
        return result
    except Exception as e:
        logger.error(
            f"Failed to send emergency session email via Celery: {str(e)}",
            extra={
                "event_type": "emergency_session_email_failed",
                "session_id": str(session_id),
                "patient_email": recipient_email,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            },
        )
        # Re-raise so Celery knows it failed (and can retry if configured)
        raise e
