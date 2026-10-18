import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification_task(self, user_id: int, subject: str, template: str, context: dict):
    try:
        user = User.objects.filter(id=user_id).first()
        if not user or not user.email:
            return

        lang = getattr(user, 'language', 'ru')
        message_body = f"Здравствуйте, {user.first_name}!\n\n{subject}\nДетали: {context}"

        if lang == 'kk':
            message_body = f"Сәлеметсіз бе, {user.first_name}!\n\n{subject}\nМәліметтер: {context}"
        elif lang == 'en':
            message_body = f"Hello, {user.first_name}!\n\n{subject}\nDetails: {context}"

        send_mail(
            subject=subject,
            message=message_body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@edu.local'),
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Email sent successfully to {user.email}")
    except Exception as exc:
        logger.error(f"Failed to send email to user_id={user_id}: {exc}")
        raise self.retry(exc=exc)
