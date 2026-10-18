from celery import shared_task

from .services import AssignmentService


@shared_task
def send_assignment_deadline_reminders():
    """Каждый час: напомнить о заданиях с дедлайном в ближайшие 24 часа."""
    return AssignmentService.send_deadline_reminders(hours_before=24)
