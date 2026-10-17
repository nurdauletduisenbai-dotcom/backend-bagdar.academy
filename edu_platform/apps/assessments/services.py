from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import Test, TestAttempt, AttemptAnswer, AttemptEventLog, TestQuestion
from apps.courses.models import Enrollment


class AssessmentService:
    @classmethod
    def start_attempt(cls, test: Test, student) -> TestAttempt:
        # Проверка активной записи
        if not student.is_superuser:
            has_enrollment = Enrollment.objects.filter(
                student=student,
                course=test.course,
                status='active',
                access_until__gte=timezone.now()
            ).exists()
            if not has_enrollment:
                raise PermissionDenied("Доступ к тесту закрыт: требуется активная запись на курс.")

        # Ограничение по датам доступности
        now = timezone.now()
        if test.available_from and now < test.available_from:
            raise ValidationError("Тест еще недоступен для сдачи.")
        if test.available_to and now > test.available_to:
            raise ValidationError("Время доступности теста истекло.")

        # Проверка на наличие уже запущенной попытки (Защита от списывания)
        active_attempt = TestAttempt.objects.filter(
            test=test,
            student=student,
            status=TestAttempt.Status.IN_PROGRESS
        ).first()
        if active_attempt:
            # Проверяем, не истек ли таймер
            elapsed = (now - active_attempt.started_at).total_seconds()
            if test.time_limit_minutes > 0 and elapsed > (test.time_limit_minutes * 60 + 60):
                # Истекла, закрываем автоматически
                active_attempt.status = TestAttempt.Status.EXPIRED
                active_attempt.submitted_at = active_attempt.started_at + timezone.timedelta(minutes=test.time_limit_minutes)
                active_attempt.save()
            else:
                return active_attempt

        # Проверка лимита числа попыток
        completed_count = TestAttempt.objects.filter(
            test=test,
            student=student,
            status__in=[TestAttempt.Status.SUBMITTED, TestAttempt.Status.GRADED, TestAttempt.Status.EXPIRED]
        ).count()
        if test.max_attempts > 0 and completed_count >= test.max_attempts:
            raise ValidationError(f"Вы исчерпали лимит попыток для этого теста ({test.max_attempts}).")

        # Создаем новую попытку
        test_questions = TestQuestion.objects.filter(test=test).select_related('question')
        total_max_score = sum(tq.points for tq in test_questions)

        attempt = TestAttempt.objects.create(
            test=test,
            student=student,
            max_score=total_max_score,
            status=TestAttempt.Status.IN_PROGRESS
        )

        return attempt

    @classmethod
    def get_clean_questions_for_student(cls, attempt: TestAttempt):
        """
        КРИТЕРИЙ ПРИЕМКИ:
        Никогда не передавать клиенту флаги is_correct и разборы ответов до сдачи теста!
        """
        test_questions = TestQuestion.objects.filter(test=attempt.test).select_related('question').prefetch_related('question__options')

        questions_payload = []
        for tq in test_questions:
            q = tq.question
            clean_options = [
                {
                    'id': opt.id,
                    'text': opt.text,
                    'match_target': opt.match_target if q.type == 'match' else None
                }
                for opt in q.options.all()
            ]

            questions_payload.append({
                'id': q.id,
                'type': q.type,
                'text': q.text,
                'points': tq.points,
                'order': tq.order,
                'options': clean_options,
            })

        return questions_payload

    @classmethod
    def save_answer(cls, attempt: TestAttempt, question_id: int, selected_options=None, text_answer=''):
        if attempt.status != TestAttempt.Status.IN_PROGRESS:
            raise ValidationError("Попытка уже завершена, сохранение ответов невозможно.")

        ans, _ = AttemptAnswer.objects.get_or_create(
            attempt=attempt,
            question_id=question_id,
            defaults={
                'selected_options': selected_options or [],
                'text_answer': text_answer or ''
            }
        )
        if selected_options is not None:
            ans.selected_options = selected_options
        if text_answer is not None:
            ans.text_answer = text_answer
        ans.save()
        return ans

    @classmethod
    def log_anti_cheat_event(cls, attempt: TestAttempt, event_type: str, metadata: dict = None):
        return AttemptEventLog.objects.create(
            attempt=attempt,
            event_type=event_type,
            metadata=metadata or {}
        )

    @classmethod
    def submit_attempt(cls, attempt: TestAttempt):
        if attempt.status != TestAttempt.Status.IN_PROGRESS:
            return attempt

        now = timezone.now()
        attempt.submitted_at = now
        attempt.time_spent_seconds = int((now - attempt.started_at).total_seconds())

        # Автоматическая проверка закрытых вопросов
        total_earned_score = 0.0
        test_questions = {tq.question_id: tq for tq in TestQuestion.objects.filter(test=attempt.test).select_related('question')}

        answers = AttemptAnswer.objects.filter(attempt=attempt).select_related('question').prefetch_related('question__options')
        answered_question_ids = set()

        for ans in answers:
            q = ans.question
            tq = test_questions.get(q.id)
            max_points = tq.points if tq else 1.0
            answered_question_ids.add(q.id)

            if q.type == 'single':
                correct_opt = q.options.filter(is_correct=True).first()
                if correct_opt and ans.selected_options and correct_opt.id in ans.selected_options:
                    ans.score = max_points
                    ans.is_correct = True
                else:
                    ans.score = 0.0
                    ans.is_correct = False

            elif q.type == 'multi':
                correct_ids = set(q.options.filter(is_correct=True).values_list('id', flat=True))
                chosen_ids = set(ans.selected_options or [])
                if correct_ids == chosen_ids:
                    ans.score = max_points
                    ans.is_correct = True
                else:
                    ans.score = 0.0
                    ans.is_correct = False

            elif q.type == 'number':
                try:
                    user_val = float(str(ans.text_answer).strip().replace(',', '.'))
                    correct_opt = q.options.filter(is_correct=True).first()
                    if correct_opt:
                        correct_val = float(correct_opt.text.strip().replace(',', '.'))
                        tolerance = q.tolerance or 0.0
                        if abs(user_val - correct_val) <= tolerance:
                            ans.score = max_points
                            ans.is_correct = True
                        else:
                            ans.score = 0.0
                            ans.is_correct = False
                except (ValueError, TypeError):
                    ans.score = 0.0
                    ans.is_correct = False

            elif q.type == 'short':
                correct_texts = [opt.text.strip().lower() for opt in q.options.filter(is_correct=True)]
                if str(ans.text_answer).strip().lower() in correct_texts:
                    ans.score = max_points
                    ans.is_correct = True
                else:
                    ans.score = 0.0
                    ans.is_correct = False

            elif q.type == 'open':
                ans.auto_graded = False
                ans.score = 0.0
                ans.is_correct = False

            ans.save()
            total_earned_score += ans.score

        attempt.score = total_earned_score
        attempt.score_pct = round((total_earned_score / max(1.0, attempt.max_score)) * 100, 1)
        attempt.is_passed = attempt.score_pct >= attempt.test.passing_score_pct
        attempt.status = TestAttempt.Status.GRADED
        attempt.save()

        return attempt
