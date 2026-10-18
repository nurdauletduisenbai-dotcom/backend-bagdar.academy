import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

logger = logging.getLogger(__name__)
User = get_user_model()

GREETINGS = {
    'ru': 'Здравствуйте, {name}!',
    'kk': 'Сәлеметсіз бе, {name}!',
    'en': 'Hello, {name}!',
}

TEMPLATES = {
    'notification': {
        'ru': '{message}',
        'kk': '{message}',
        'en': '{message}',
    },
    'password_reset': {
        'ru': 'Чтобы задать новый пароль, перейдите по ссылке (действует 1 час):\n{link}\n\n'
              'Если вы не запрашивали сброс — просто проигнорируйте письмо.',
        'kk': 'Жаңа құпиясөз орнату үшін сілтеме бойынша өтіңіз (1 сағат жарамды):\n{link}',
        'en': 'To set a new password, open this link (valid for 1 hour):\n{link}',
    },
    'verify_email': {
        'ru': 'Чтобы подтвердить email, перейдите по ссылке (действует 24 часа):\n{link}',
        'kk': 'Email-ді растау үшін сілтеме бойынша өтіңіз (24 сағат жарамды):\n{link}',
        'en': 'To confirm your email, open this link (valid for 24 hours):\n{link}',
    },
}


def render_message(template: str, lang: str, name: str, context: dict) -> str:
    lang = lang if lang in GREETINGS else 'ru'
    greeting = GREETINGS[lang].format(name=name)
    body_template = TEMPLATES.get(template, {}).get(lang)
    if body_template:
        body = body_template.format(**context)
    else:
        body = '\n'.join(f'{key}: {value}' for key, value in context.items())
    return f'{greeting}\n\n{body}\n\n— EduPlatform'


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification_task(self, user_id: int, subject: str, template: str, context: dict):
    user = User.objects.filter(id=user_id).first()
    if not user or not user.email:
        return

    message = render_message(template, getattr(user, 'language', 'ru'), user.first_name, context)
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@edu.local'),
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info('Email "%s" sent to user_id=%s', template, user_id)
    except Exception as exc:  # noqa: BLE001 — любая ошибка SMTP -> повтор
        logger.error('Failed to send email to user_id=%s: %s', user_id, exc)
        raise self.retry(exc=exc) from exc
