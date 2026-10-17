from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .models import Test, TestAttempt
from .services import AssessmentService


class StartTestAttemptView(APIView):
    """
    Старт попытки прохождения теста.
    Возвращает структуру теста и вариантов вопросов БЕЗ правильных ответов.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, test_id):
        test = Test.objects.select_related('course').get(id=test_id)
        attempt = AssessmentService.start_attempt(test, request.user)
        clean_questions = AssessmentService.get_clean_questions_for_student(attempt)

        return Response({
            'attempt_id': attempt.id,
            'test_id': test.id,
            'title': test.title,
            'time_limit_minutes': test.time_limit_minutes,
            'started_at': attempt.started_at,
            'max_score': attempt.max_score,
            'status': attempt.status,
            'questions': clean_questions,
        }, status=status.HTTP_201_CREATED)


class SaveAttemptAnswerView(APIView):
    """Автосохранение ответа на конкретный вопрос в процессе прохождения"""
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, attempt_id, question_id):
        attempt = TestAttempt.objects.get(id=attempt_id, student=request.user)
        selected_options = request.data.get('selected_options')
        text_answer = request.data.get('text_answer', '')

        AssessmentService.save_answer(
            attempt=attempt,
            question_id=question_id,
            selected_options=selected_options,
            text_answer=text_answer
        )
        return Response({'message': 'Ответ сохранен.'}, status=status.HTTP_200_OK)


class LogAntiCheatEventView(APIView):
    """Журналирование событий античита (потеря фокуса вкладки, copy-paste)"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, attempt_id):
        attempt = TestAttempt.objects.get(id=attempt_id, student=request.user)
        event_type = request.data.get('event_type', 'tab_blur')
        metadata = request.data.get('metadata', {})
        AssessmentService.log_anti_cheat_event(attempt, event_type, metadata)
        return Response({'status': 'logged'}, status=status.HTTP_200_OK)


class SubmitTestAttemptView(APIView):
    """
    Сдача теста: расчет баллов, автопроверка закрытых типов, возврат результата.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, attempt_id):
        attempt = TestAttempt.objects.select_related('test').get(id=attempt_id, student=request.user)
        graded_attempt = AssessmentService.submit_attempt(attempt)

        return Response({
            'attempt_id': graded_attempt.id,
            'status': graded_attempt.status,
            'score': graded_attempt.score,
            'max_score': graded_attempt.max_score,
            'score_pct': graded_attempt.score_pct,
            'is_passed': graded_attempt.is_passed,
            'time_spent_seconds': graded_attempt.time_spent_seconds,
            'submitted_at': graded_attempt.submitted_at,
        })
