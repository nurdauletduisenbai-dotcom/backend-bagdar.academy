import random
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.common.permissions import STAFF_ROLES
from apps.courses.models import Enrollment
from apps.questions.models import Question

from .models import AttemptAnswer, AttemptEventLog, Test, TestAttempt, TestQuestion

# Сетевая задержка: после окончания таймера ещё столько секунд принимаем ответы
GRACE_SECONDS = 60
ANTI_CHEAT_EVENTS = {'tab_blur', 'tab_focus', 'window_resize', 'copy_paste', 'fullscreen_exit', 'devtools_open'}
FINISHED_STATUSES = (TestAttempt.Status.SUBMITTED, TestAttempt.Status.GRADED, TestAttempt.Status.EXPIRED)


def _norm_number(value) -> float:
    return float(str(value).strip().replace(',', '.'))


class AssessmentService:
    # ---------- Таймер ----------

    @classmethod
    def deadline(cls, attempt: TestAttempt):
        minutes = attempt.test.time_limit_minutes
        return attempt.started_at + timedelta(minutes=minutes) if minutes > 0 else None

    @classmethod
    def is_overdue(cls, attempt: TestAttempt, now=None) -> bool:
        deadline = cls.deadline(attempt)
        return bool(deadline) and (now or timezone.now()) > deadline + timedelta(seconds=GRACE_SECONDS)

    @classmethod
    def ensure_in_progress(cls, attempt: TestAttempt):
        """Ответы принимаются только в активной попытке и только до конца таймера."""
        if attempt.status != TestAttempt.Status.IN_PROGRESS:
            raise ValidationError('Попытка уже завершена, сохранение ответов невозможно.')
        if cls.is_overdue(attempt):
            cls.finalize(attempt, expired=True)
            raise ValidationError('Время на тест истекло. Попытка завершена автоматически.')

    # ---------- Старт ----------

    @classmethod
    def start_attempt(cls, test: Test, student) -> TestAttempt:
        if not student.is_superuser:
            has_enrollment = Enrollment.objects.filter(
                student=student,
                course=test.course,
                status=Enrollment.Status.ACTIVE,
                access_until__gte=timezone.now(),
            ).exists()
            if not has_enrollment:
                raise PermissionDenied('Доступ к тесту закрыт: требуется активная запись на курс.')

        now = timezone.now()
        if test.available_from and now < test.available_from:
            raise ValidationError('Тест еще недоступен для сдачи.')
        if test.available_to and now > test.available_to:
            raise ValidationError('Время доступности теста истекло.')

        with transaction.atomic():
            active_attempt = (
                TestAttempt.objects.select_for_update()
                .select_related('test')
                .filter(test=test, student=student, status=TestAttempt.Status.IN_PROGRESS)
                .first()
            )
            if active_attempt:
                if not cls.is_overdue(active_attempt, now):
                    return active_attempt  # продолжаем ту же попытку с тем же порядком вопросов
                cls.finalize(active_attempt, expired=True)

            completed_count = TestAttempt.objects.filter(
                test=test, student=student, status__in=FINISHED_STATUSES
            ).count()
            if test.max_attempts > 0 and completed_count >= test.max_attempts:
                raise ValidationError(f'Вы исчерпали лимит попыток для этого теста ({test.max_attempts}).')

            test_questions = list(
                TestQuestion.objects.filter(test=test).select_related('question').prefetch_related('question__options')
            )
            if not test_questions:
                raise ValidationError('В тесте пока нет вопросов.')

            question_order = [tq.question_id for tq in test_questions]
            if test.shuffle_questions:
                random.shuffle(question_order)

            option_order = {}
            for tq in test_questions:
                ids = [opt.id for opt in tq.question.options.all()]
                if test.shuffle_options:
                    random.shuffle(ids)
                option_order[str(tq.question_id)] = ids

            return TestAttempt.objects.create(
                test=test,
                student=student,
                max_score=sum(tq.points for tq in test_questions),
                status=TestAttempt.Status.IN_PROGRESS,
                question_order=question_order,
                option_order=option_order,
            )

    @classmethod
    def get_clean_questions_for_student(cls, attempt: TestAttempt) -> list[dict]:
        """
        КРИТЕРИЙ ПРИЕМКИ: клиент не получает is_correct, разборы и тексты правильных ответов до сдачи.
        Для short/number варианты не отдаются вовсе (их тексты — это и есть ответы),
        для match цели сопоставления отдаются отдельным перемешанным списком.
        """
        test_questions = {
            tq.question_id: tq
            for tq in TestQuestion.objects.filter(test=attempt.test)
            .select_related('question')
            .prefetch_related('question__options')
        }
        saved = {a.question_id: a for a in AttemptAnswer.objects.filter(attempt=attempt)}
        order = [qid for qid in attempt.question_order if qid in test_questions] or list(test_questions)
        rng = random.Random(attempt.id)

        payload = []
        for position, qid in enumerate(order, start=1):
            tq = test_questions[qid]
            q = tq.question
            options_by_id = {opt.id: opt for opt in q.options.all()}
            ordered_ids = [i for i in attempt.option_order.get(str(qid), []) if i in options_by_id]
            ordered_ids += [i for i in options_by_id if i not in ordered_ids]

            item = {
                'id': q.id,
                'type': q.type,
                'text': q.text,
                'points': tq.points,
                'order': position,
                'options': [],
            }
            if q.type in (Question.Type.SINGLE, Question.Type.MULTI, Question.Type.MATCH):
                item['options'] = [{'id': i, 'text': options_by_id[i].text} for i in ordered_ids]
            if q.type == Question.Type.MATCH:
                targets = sorted({opt.match_target for opt in options_by_id.values() if opt.match_target})
                rng.shuffle(targets)
                item['match_targets'] = targets

            answer = saved.get(qid)
            item['saved_answer'] = (
                {'selected_options': answer.selected_options, 'text_answer': answer.text_answer} if answer else None
            )
            payload.append(item)
        return payload

    # ---------- Ответы ----------

    @classmethod
    def save_answer(cls, attempt: TestAttempt, question_id: int, selected_options=None, text_answer=None):
        cls.ensure_in_progress(attempt)

        tq = TestQuestion.objects.filter(test=attempt.test, question_id=question_id).select_related('question').first()
        if not tq:
            raise NotFound('Вопрос не относится к этому тесту.')
        q = tq.question
        option_ids = set(q.options.values_list('id', flat=True))

        if q.type in (Question.Type.SINGLE, Question.Type.MULTI):
            if selected_options is None:
                selected_options = []
            if not isinstance(selected_options, list) or not all(isinstance(i, int) for i in selected_options):
                raise ValidationError({'selected_options': 'Ожидается список ID вариантов.'})
            if not set(selected_options) <= option_ids:
                raise ValidationError({'selected_options': 'Вариант не относится к этому вопросу.'})
            if q.type == Question.Type.SINGLE and len(selected_options) > 1:
                raise ValidationError({'selected_options': 'В этом вопросе можно выбрать только один вариант.'})
            selected_options = sorted(set(selected_options))
            text_answer = ''
        elif q.type == Question.Type.MATCH:
            if not isinstance(selected_options, dict):
                raise ValidationError({'selected_options': 'Ожидается объект {ID варианта: цель сопоставления}.'})
            try:
                selected_options = {str(int(k)): str(v) for k, v in selected_options.items()}
            except (TypeError, ValueError) as exc:
                raise ValidationError({'selected_options': 'Ключи должны быть ID вариантов.'}) from exc
            if not {int(k) for k in selected_options} <= option_ids:
                raise ValidationError({'selected_options': 'Вариант не относится к этому вопросу.'})
            text_answer = ''
        else:
            selected_options = []
            text_answer = (text_answer or '').strip()
            if q.type == Question.Type.NUMBER and text_answer:
                try:
                    _norm_number(text_answer)
                except ValueError as exc:
                    raise ValidationError({'text_answer': 'Ожидается число.'}) from exc

        answer, _ = AttemptAnswer.objects.update_or_create(
            attempt=attempt,
            question=q,
            defaults={'selected_options': selected_options, 'text_answer': text_answer},
        )
        return answer

    @classmethod
    def log_anti_cheat_event(cls, attempt: TestAttempt, event_type: str, metadata: dict | None = None):
        if attempt.status != TestAttempt.Status.IN_PROGRESS:
            raise ValidationError('Попытка уже завершена.')
        if event_type not in ANTI_CHEAT_EVENTS:
            raise ValidationError({'event_type': f'Допустимые события: {", ".join(sorted(ANTI_CHEAT_EVENTS))}.'})
        return AttemptEventLog.objects.create(attempt=attempt, event_type=event_type, metadata=metadata or {})

    # ---------- Проверка ----------

    @classmethod
    def grade_answer(cls, answer: AttemptAnswer, max_points: float):
        q = answer.question
        options = list(q.options.all())
        correct = False

        if q.type == Question.Type.SINGLE:
            correct_ids = {o.id for o in options if o.is_correct}
            correct = len(answer.selected_options or []) == 1 and set(answer.selected_options) <= correct_ids
        elif q.type == Question.Type.MULTI:
            correct_ids = {o.id for o in options if o.is_correct}
            correct = bool(correct_ids) and set(answer.selected_options or []) == correct_ids
        elif q.type == Question.Type.NUMBER:
            try:
                user_val = _norm_number(answer.text_answer)
                correct = any(
                    abs(user_val - _norm_number(o.text)) <= (q.tolerance or 0.0) for o in options if o.is_correct
                )
            except (TypeError, ValueError):
                correct = False
        elif q.type == Question.Type.SHORT:
            correct_texts = {o.text.strip().lower() for o in options if o.is_correct}
            correct = (answer.text_answer or '').strip().lower() in correct_texts
        elif q.type == Question.Type.MATCH:
            chosen = answer.selected_options if isinstance(answer.selected_options, dict) else {}
            pairs = [o for o in options if o.match_target]
            correct = bool(pairs) and all(
                chosen.get(str(o.id), '').strip().lower() == o.match_target.strip().lower() for o in pairs
            )
        elif q.type == Question.Type.OPEN:
            answer.auto_graded = False
            answer.is_correct = False
            answer.score = 0.0
            return

        answer.auto_graded = True
        answer.is_correct = correct
        answer.score = max_points if correct else 0.0

    @classmethod
    def recalculate(cls, attempt: TestAttempt):
        earned = sum(AttemptAnswer.objects.filter(attempt=attempt).values_list('score', flat=True))
        attempt.score = earned
        attempt.score_pct = round(earned / attempt.max_score * 100, 1) if attempt.max_score else 0.0
        attempt.is_passed = attempt.score_pct >= attempt.test.passing_score_pct

    @classmethod
    @transaction.atomic
    def finalize(cls, attempt: TestAttempt, expired: bool = False) -> TestAttempt:
        """Автопроверка закрытых вопросов. Открытые ждут проверки учителем (статус submitted)."""
        now = timezone.now()
        deadline = cls.deadline(attempt)
        attempt.submitted_at = min(now, deadline) if (expired and deadline) else now
        attempt.time_spent_seconds = int((attempt.submitted_at - attempt.started_at).total_seconds())

        test_questions = {tq.question_id: tq for tq in TestQuestion.objects.filter(test=attempt.test)}
        has_open = Question.objects.filter(id__in=test_questions, type=Question.Type.OPEN).exists()

        answers = AttemptAnswer.objects.filter(attempt=attempt, question_id__in=test_questions)
        for answer in answers.select_related('question').prefetch_related('question__options'):
            cls.grade_answer(answer, test_questions[answer.question_id].points)
            answer.save(update_fields=['score', 'is_correct', 'auto_graded', 'updated_at'])

        cls.recalculate(attempt)
        if expired:
            attempt.status = TestAttempt.Status.EXPIRED
        else:
            attempt.status = TestAttempt.Status.SUBMITTED if has_open else TestAttempt.Status.GRADED
        attempt.save()
        cls.after_result_changed(attempt)
        return attempt

    @classmethod
    def after_result_changed(cls, attempt: TestAttempt):
        """Пересчёт прогресса курса и уведомление ученика о результате."""
        from apps.notifications.services import NotificationService
        from apps.progress.services import ProgressService

        ProgressService.recalculate(attempt.student, attempt.test.course)
        if attempt.status in (TestAttempt.Status.GRADED, TestAttempt.Status.EXPIRED):
            NotificationService.notify(
                [attempt.student], NotificationService.Type.TEST_RESULT,
                title=f'Результат теста «{attempt.test.title}»',
                message=f'{attempt.score:g} из {attempt.max_score:g} ({attempt.score_pct}%).'
                        + (' Тест пройден.' if attempt.is_passed else ''),
                metadata={'test_id': attempt.test_id, 'attempt_id': attempt.id},
            )

    @classmethod
    def submit_attempt(cls, attempt: TestAttempt) -> TestAttempt:
        if attempt.status != TestAttempt.Status.IN_PROGRESS:
            return attempt
        return cls.finalize(attempt, expired=cls.is_overdue(attempt))

    @classmethod
    @transaction.atomic
    def grade_open_answer(cls, attempt: TestAttempt, question_id: int, score: float, feedback: str = ''):
        if attempt.status == TestAttempt.Status.IN_PROGRESS:
            raise ValidationError('Попытка ещё не сдана.')
        tq = TestQuestion.objects.filter(test=attempt.test, question_id=question_id).first()
        if not tq:
            raise NotFound('Вопрос не относится к этому тесту.')
        if not 0 <= score <= tq.points:
            raise ValidationError({'score': f'Балл должен быть от 0 до {tq.points}.'})

        answer, _ = AttemptAnswer.objects.get_or_create(attempt=attempt, question_id=question_id)
        answer.score = score
        answer.is_correct = score == tq.points
        answer.auto_graded = False
        answer.teacher_feedback = feedback
        answer.teacher_graded_at = timezone.now()
        answer.save()

        cls.recalculate(attempt)
        pending_open = TestQuestion.objects.filter(test=attempt.test, question__type=Question.Type.OPEN).exclude(
            question_id__in=AttemptAnswer.objects.filter(
                attempt=attempt, teacher_graded_at__isnull=False
            ).values('question_id')
        )
        if attempt.status == TestAttempt.Status.SUBMITTED and not pending_open.exists():
            attempt.status = TestAttempt.Status.GRADED
        attempt.save()
        cls.after_result_changed(attempt)
        return attempt

    # ---------- Результаты ----------

    @classmethod
    def is_staff_for_test(cls, test: Test, user) -> bool:
        return any(r in STAFF_ROLES for r in user.get_roles_for_org(test.course.org_id))

    @classmethod
    def result_payload(cls, attempt: TestAttempt, include_review: bool) -> dict:
        data = {
            'attempt_id': attempt.id,
            'test_id': attempt.test_id,
            'status': attempt.status,
            'score': attempt.score,
            'max_score': attempt.max_score,
            'score_pct': attempt.score_pct,
            'is_passed': attempt.is_passed,
            'started_at': attempt.started_at,
            'submitted_at': attempt.submitted_at,
            'time_spent_seconds': attempt.time_spent_seconds,
            'review': None,
        }
        if not include_review or attempt.status == TestAttempt.Status.IN_PROGRESS:
            return data

        answers = {a.question_id: a for a in AttemptAnswer.objects.filter(attempt=attempt)}
        review = []
        for tq in TestQuestion.objects.filter(test=attempt.test).select_related('question').prefetch_related(
            'question__options'
        ):
            q = tq.question
            a = answers.get(q.id)
            review.append({
                'question_id': q.id,
                'type': q.type,
                'text': q.text,
                'points': tq.points,
                'explanation': q.explanation,
                'options': [{'id': o.id, 'text': o.text} for o in q.options.all()],
                'correct_options': [
                    {'id': o.id, 'text': o.text, 'match_target': o.match_target or None}
                    for o in q.options.all() if o.is_correct or (q.type == Question.Type.MATCH and o.match_target)
                ],
                'selected_options': a.selected_options if a else [],
                'text_answer': a.text_answer if a else '',
                'score': a.score if a else 0.0,
                'is_correct': a.is_correct if a else False,
                'teacher_feedback': a.teacher_feedback if a else '',
            })
        data['review'] = review
        return data


class TestBuilderService:
    @classmethod
    def ensure_editable(cls, test: Test):
        """Состав теста нельзя менять, когда уже есть сданные попытки — иначе результаты станут несопоставимы."""
        if test.attempts.filter(status__in=FINISHED_STATUSES).exists():
            raise ValidationError('По тесту уже есть сданные попытки — создайте новый тест или копию.')

    @classmethod
    def add_question(cls, test: Test, question: Question, points: float, order: int | None = None) -> TestQuestion:
        cls.ensure_editable(test)
        if question.topic.org_id != test.course.org_id:
            raise ValidationError({'question_id': 'Вопрос из банка другой организации.'})
        if question.is_archived:
            raise ValidationError({'question_id': 'Вопрос в архиве.'})
        if order is None:
            order = (test.test_questions.order_by('-order').values_list('order', flat=True).first() or 0) + 1
        tq, created = TestQuestion.objects.get_or_create(
            test=test, question=question, defaults={'points': points, 'order': order}
        )
        if not created:
            raise ValidationError({'question_id': 'Вопрос уже есть в тесте.'})
        return tq

    @classmethod
    def stats(cls, test: Test) -> dict:
        from django.db.models import Avg, Count

        finished = test.attempts.filter(status__in=FINISHED_STATUSES)
        agg = finished.aggregate(avg_pct=Avg('score_pct'), n=Count('id'), students=Count('student', distinct=True))
        passed = finished.filter(is_passed=True).count()

        per_question = []
        for tq in test.test_questions.select_related('question').order_by('order', 'id'):
            answers = AttemptAnswer.objects.filter(attempt__in=finished, question=tq.question)
            total = answers.count()
            correct = answers.filter(is_correct=True).count()
            per_question.append({
                'question_id': tq.question_id,
                'text': tq.question.text[:120],
                'type': tq.question.type,
                'answered': total,
                'correct_pct': round(correct / total * 100, 1) if total else None,
            })
        return {
            'test_id': test.id,
            'attempts': agg['n'] or 0,
            'students': agg['students'] or 0,
            'average_score_pct': round(agg['avg_pct'] or 0.0, 1),
            'pass_rate_pct': round(passed / agg['n'] * 100, 1) if agg['n'] else 0.0,
            'anti_cheat_events': AttemptEventLog.objects.filter(attempt__test=test).count(),
            'questions': per_question,
        }
