from celery import shared_task

from .services import ScheduleService


@shared_task
def send_session_reminders():
    """Каждые 5 минут: напомнить о занятиях, которые начнутся в ближайшие 30 минут."""
    return ScheduleService.send_session_reminders(minutes_before=30)
