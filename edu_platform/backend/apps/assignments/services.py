from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.common.files import validate_upload
from apps.courses.access import active_student_ids, has_active_enrollment
from apps.notifications.services import NotificationService

from .models import Assignment, AssignmentSubmission


class AssignmentService:
    @classmethod
    def course_of(cls, assignment: Assignment):
        return assignment.lesson.section.course

    @classmethod
    def notify_new(cls, assignment: Assignment):
        from apps.accounts.models import User
        students = User.objects.filter(id__in=active_student_ids(cls.course_of(assignment)))
        NotificationService.notify(
            students, NotificationService.Type.ASSIGNMENT_NEW,
            title=f'Новое задание: {assignment.title}',
            message=f'Срок сдачи: {timezone.localtime(assignment.deadline):%d.%m.%Y %H:%M}.',
            metadata={'assignment_id': assignment.id, 'lesson_id': assignment.lesson_id},
            email=True,
        )

    @classmethod
    @transaction.atomic
    def submit(cls, assignment: Assignment, student, text_content='', file=None, file_url=None) -> AssignmentSubmission:
        if not has_active_enrollment(student, cls.course_of(assignment)):
            raise PermissionDenied('Сдавать задания могут только записанные на курс ученики.')
        if not (text_content or file or file_url):
            raise ValidationError('Добавьте текст ответа, файл или ссылку.')
        validate_upload(file)

        now = timezone.now()
        is_late = now > assignment.deadline
        if is_late and not assignment.accept_late:
            raise ValidationError('Срок сдачи истёк, задание больше не принимается.')

        submission = AssignmentSubmission.objects.select_for_update().filter(
            assignment=assignment, student=student
        ).first()
        if submission:
            locked = submission.status == AssignmentSubmission.Status.GRADED and not submission.can_resubmit
            if locked:
                raise ValidationError('Работа уже проверена. Пересдача возможна, только если её разрешит учитель.')
        else:
            submission = AssignmentSubmission(assignment=assignment, student=student)

        submission.text_content = text_content or ''
        if file:
            submission.file = file
        submission.file_url = file_url or None
        submission.is_late = is_late
        submission.status = AssignmentSubmission.Status.SUBMITTED
        submission.score = None
        submission.graded_at = None
        submission.graded_by = None
        submission.can_resubmit = False
        submission.save()
        if submission.pk:
            AssignmentSubmission.objects.filter(pk=submission.pk).update(submitted_at=now)
            submission.submitted_at = now
        return submission

    @classmethod
    def grade(cls, submission: AssignmentSubmission, teacher, score: float, feedback: str = '',
              can_resubmit: bool = False) -> AssignmentSubmission:
        max_score = submission.assignment.max_score
        if not 0 <= score <= max_score:
            raise ValidationError({'score': f'Балл должен быть от 0 до {max_score}.'})
        submission.score = score
        submission.feedback = feedback
        submission.can_resubmit = can_resubmit
        submission.status = (AssignmentSubmission.Status.RETURNED if can_resubmit
                             else AssignmentSubmission.Status.GRADED)
        submission.graded_by = teacher
        submission.graded_at = timezone.now()
        submission.save()

        NotificationService.notify(
            [submission.student], NotificationService.Type.ASSIGNMENT_GRADED,
            title=f'Задание «{submission.assignment.title}» проверено',
            message=f'Оценка: {score:g} из {max_score}.' + (' Можно пересдать.' if can_resubmit else ''),
            metadata={'assignment_id': submission.assignment_id, 'submission_id': submission.id},
            email=True,
        )
        return submission

    @classmethod
    def send_deadline_reminders(cls, hours_before: int = 24) -> int:
        """Напоминание ученикам, которые ещё не сдали задание с дедлайном в ближайшие N часов."""
        from apps.accounts.models import User
        now = timezone.now()
        sent = 0
        upcoming = Assignment.objects.filter(deadline__gt=now, deadline__lte=now + timedelta(hours=hours_before))
        for assignment in upcoming.select_related('lesson__section__course'):
            submitted = set(assignment.submissions.values_list('student_id', flat=True))
            for student in User.objects.filter(id__in=active_student_ids(cls.course_of(assignment))):
                if student.id in submitted:
                    continue
                if NotificationService.already_sent(student.id, NotificationService.Type.ASSIGNMENT_DEADLINE,
                                                    assignment_id=assignment.id):
                    continue
                sent += NotificationService.notify(
                    [student], NotificationService.Type.ASSIGNMENT_DEADLINE,
                    title=f'Скоро дедлайн: {assignment.title}',
                    message=f'Сдайте до {timezone.localtime(assignment.deadline):%d.%m.%Y %H:%M}.',
                    metadata={'assignment_id': assignment.id},
                    email=True,
                )
        return sent
