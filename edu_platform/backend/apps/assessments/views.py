from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.serializers import MessageSerializer
from apps.questions.models import Question

from .models import Test, TestAttempt
from .services import ANTI_CHEAT_EVENTS, AssessmentService

# ---------- Схемы запросов/ответов ----------


class TestInfoSerializer(serializers.ModelSerializer):
    attempts_used = serializers.SerializerMethodField()
    questions_count = serializers.IntegerField(source='test_questions.count', read_only=True)

    class Meta:
        model = Test
        fields = (
            'id', 'course', 'lesson', 'title', 'description', 'mode', 'time_limit_minutes', 'max_attempts',
            'passing_score_pct', 'show_answers_after_submit', 'available_from', 'available_to',
            'questions_count', 'attempts_used',
        )

    def get_attempts_used(self, obj) -> int:
        user = self.context['request'].user
        return obj.attempts.filter(student=user).exclude(status=TestAttempt.Status.IN_PROGRESS).count()


class QuestionOptionPublicSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()


class AttemptQuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=Question.Type.choices)
    text = serializers.CharField(help_text='Markdown / LaTeX')
    points = serializers.FloatField()
    order = serializers.IntegerField()
    options = QuestionOptionPublicSerializer(many=True, help_text='Пусто для short/number/open')
    match_targets = serializers.ListField(child=serializers.CharField(), required=False,
                                          help_text='Только для match: цели сопоставления')
    saved_answer = serializers.JSONField(allow_null=True)


class AttemptStartedSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    test_id = serializers.IntegerField()
    title = serializers.CharField()
    time_limit_minutes = serializers.IntegerField()
    started_at = serializers.DateTimeField()
    deadline = serializers.DateTimeField(allow_null=True)
    max_score = serializers.FloatField()
    status = serializers.CharField()
    questions = AttemptQuestionSerializer(many=True)


class SaveAnswerSerializer(serializers.Serializer):
    selected_options = serializers.JSONField(
        required=False,
        help_text='single/multi: [id, ...]; match: {"<option_id>": "<цель>"}',
    )
    text_answer = serializers.CharField(required=False, allow_blank=True, help_text='short/number/open')


class AntiCheatEventSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=sorted(ANTI_CHEAT_EVENTS))
    metadata = serializers.DictField(required=False)


class GradeAnswerSerializer(serializers.Serializer):
    score = serializers.FloatField(min_value=0)
    feedback = serializers.CharField(required=False, allow_blank=True, default='')


class AttemptResultSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    test_id = serializers.IntegerField()
    status = serializers.CharField()
    score = serializers.FloatField()
    max_score = serializers.FloatField()
    score_pct = serializers.FloatField()
    is_passed = serializers.BooleanField()
    started_at = serializers.DateTimeField()
    submitted_at = serializers.DateTimeField(allow_null=True)
    time_spent_seconds = serializers.IntegerField()
    review = serializers.ListField(child=serializers.DictField(), allow_null=True,
                                   help_text='Разбор ответов (если разрешён show_answers_after_submit)')


class AttemptListItemSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source='student.email', read_only=True)

    class Meta:
        model = TestAttempt
        fields = ('id', 'student', 'student_email', 'status', 'score', 'max_score', 'score_pct', 'is_passed',
                  'started_at', 'submitted_at')


# ---------- Хелперы доступа ----------


def _get_test(test_id: int) -> Test:
    return get_object_or_404(Test.objects.select_related('course'), id=test_id, course__deleted_at__isnull=True)


def _get_own_attempt(request, attempt_id: int) -> TestAttempt:
    return get_object_or_404(TestAttempt.objects.select_related('test__course'), id=attempt_id, student=request.user)


def _get_attempt_for_viewer(request, attempt_id: int) -> tuple[TestAttempt, bool]:
    """Попытку видит её автор и персонал организации курса. Возвращает (попытка, is_staff)."""
    attempt = get_object_or_404(TestAttempt.objects.select_related('test__course'), id=attempt_id)
    is_staff = AssessmentService.is_staff_for_test(attempt.test, request.user)
    if attempt.student_id != request.user.id and not is_staff:
        raise NotFound('Попытка не найдена.')
    return attempt, is_staff


def _started_payload(attempt: TestAttempt) -> dict:
    return {
        'attempt_id': attempt.id,
        'test_id': attempt.test_id,
        'title': attempt.test.title,
        'time_limit_minutes': attempt.test.time_limit_minutes,
        'started_at': attempt.started_at,
        'deadline': AssessmentService.deadline(attempt),
        'max_score': attempt.max_score,
        'status': attempt.status,
        'questions': AssessmentService.get_clean_questions_for_student(attempt),
    }


# ---------- Views ----------


@extend_schema(tags=['tests'])
class TestDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Информация о тесте', responses={200: TestInfoSerializer})
    def get(self, request, test_id):
        test = _get_test(test_id)
        return Response(TestInfoSerializer(test, context={'request': request}).data)


@extend_schema(tags=['tests'])
class StartTestAttemptView(APIView):
    """Старт (или продолжение активной) попытки. Правильные ответы не передаются."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Начать или продолжить попытку', request=None, responses={201: AttemptStartedSerializer})
    def post(self, request, test_id):
        attempt = AssessmentService.start_attempt(_get_test(test_id), request.user)
        return Response(_started_payload(attempt), status=status.HTTP_201_CREATED)

    @extend_schema(summary='Попытки теста: свои (ученик) или все (персонал)',
                   responses={200: AttemptListItemSerializer(many=True)})
    def get(self, request, test_id):
        test = _get_test(test_id)
        qs = test.attempts.select_related('student')
        if not AssessmentService.is_staff_for_test(test, request.user):
            qs = qs.filter(student=request.user)
        return Response(AttemptListItemSerializer(qs.order_by('-started_at'), many=True).data)


@extend_schema(tags=['tests'])
class AttemptDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Состояние попытки: вопросы (если идёт) или результат с разбором (если сдана)',
        responses={200: OpenApiResponse(description='AttemptStarted (in_progress) или AttemptResult')},
    )
    def get(self, request, attempt_id):
        attempt, is_staff = _get_attempt_for_viewer(request, attempt_id)
        if attempt.status == TestAttempt.Status.IN_PROGRESS:
            if AssessmentService.is_overdue(attempt):
                attempt = AssessmentService.finalize(attempt, expired=True)
            elif attempt.student_id == request.user.id:
                return Response(_started_payload(attempt))
        include_review = is_staff or attempt.test.show_answers_after_submit
        return Response(AssessmentService.result_payload(attempt, include_review))


@extend_schema(tags=['tests'])
class SaveAttemptAnswerView(APIView):
    """Автосохранение ответа на вопрос во время прохождения."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Сохранить ответ', request=SaveAnswerSerializer, responses={200: MessageSerializer})
    def put(self, request, attempt_id, question_id):
        serializer = SaveAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AssessmentService.save_answer(
            attempt=_get_own_attempt(request, attempt_id),
            question_id=question_id,
            selected_options=serializer.validated_data.get('selected_options'),
            text_answer=serializer.validated_data.get('text_answer'),
        )
        return Response({'message': 'Ответ сохранен.'}, status=status.HTTP_200_OK)


@extend_schema(tags=['tests'])
class LogAntiCheatEventView(APIView):
    """Журнал античита: потеря фокуса вкладки, copy-paste, выход из полноэкранного режима."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Записать событие античита', request=AntiCheatEventSerializer,
                   responses={200: MessageSerializer})
    def post(self, request, attempt_id):
        serializer = AntiCheatEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AssessmentService.log_anti_cheat_event(
            _get_own_attempt(request, attempt_id),
            serializer.validated_data['event_type'],
            serializer.validated_data.get('metadata'),
        )
        return Response({'message': 'Событие записано.'}, status=status.HTTP_200_OK)


@extend_schema(tags=['tests'])
class SubmitTestAttemptView(APIView):
    """Сдача теста: автопроверка закрытых вопросов, открытые ждут учителя."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Сдать попытку', request=None, responses={200: AttemptResultSerializer})
    def post(self, request, attempt_id):
        attempt = AssessmentService.submit_attempt(_get_own_attempt(request, attempt_id))
        return Response(AssessmentService.result_payload(attempt, attempt.test.show_answers_after_submit))


@extend_schema(tags=['tests'])
class GradeAttemptAnswerView(APIView):
    """Ручная проверка ответа (открытые вопросы) учителем организации курса."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Оценить ответ (учитель)', request=GradeAnswerSerializer,
                   responses={200: AttemptResultSerializer})
    def put(self, request, attempt_id, question_id):
        attempt, is_staff = _get_attempt_for_viewer(request, attempt_id)
        if not is_staff:
            raise PermissionDenied('Оценивать ответы может только персонал организации.')
        serializer = GradeAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = AssessmentService.grade_open_answer(
            attempt, question_id, serializer.validated_data['score'], serializer.validated_data['feedback']
        )
        return Response(AssessmentService.result_payload(attempt, include_review=True))
