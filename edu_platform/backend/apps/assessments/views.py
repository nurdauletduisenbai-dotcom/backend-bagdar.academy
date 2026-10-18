from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.serializers import MessageSerializer
from apps.common.viewsets import CourseScopedViewSet
from apps.content.models import Lesson
from apps.courses.models import Course
from apps.questions.models import Question
from apps.questions.serializers import QuestionSerializer

from .models import Test, TestAttempt, TestQuestion
from .services import ANTI_CHEAT_EVENTS, AssessmentService, TestBuilderService

# ---------- Схемы запросов/ответов ----------


class TestInfoSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all(), required=False, allow_null=True)
    attempts_used = serializers.SerializerMethodField()
    questions_count = serializers.IntegerField(source='test_questions.count', read_only=True)

    class Meta:
        model = Test
        fields = (
            'id', 'course', 'lesson', 'title', 'description', 'mode', 'time_limit_minutes', 'max_attempts',
            'passing_score_pct', 'shuffle_questions', 'shuffle_options', 'show_answers_after_submit',
            'available_from', 'available_to', 'questions_count', 'attempts_used', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def get_attempts_used(self, obj) -> int:
        user = self.context['request'].user
        return obj.attempts.filter(student=user).exclude(status=TestAttempt.Status.IN_PROGRESS).count()

    def validate(self, attrs):
        course = attrs.get('course') or (self.instance and self.instance.course)
        lesson = attrs.get('lesson', self.instance.lesson if self.instance else None)
        if lesson and lesson.section.course_id != course.id:
            raise serializers.ValidationError({'lesson': 'Урок из другого курса.'})
        start = attrs.get('available_from', self.instance.available_from if self.instance else None)
        finish = attrs.get('available_to', self.instance.available_to if self.instance else None)
        if start and finish and start >= finish:
            raise serializers.ValidationError({'available_to': 'Должно быть позже available_from.'})
        if not 0 <= attrs.get('passing_score_pct', 0) <= 100:
            raise serializers.ValidationError({'passing_score_pct': 'От 0 до 100.'})
        return attrs


class TestQuestionManageSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = TestQuestion
        fields = ('id', 'question', 'points', 'order')


class AddTestQuestionSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    points = serializers.FloatField(min_value=0, default=1.0)
    order = serializers.IntegerField(min_value=1, required=False)


class UpdateTestQuestionSerializer(serializers.Serializer):
    points = serializers.FloatField(min_value=0, required=False)
    order = serializers.IntegerField(min_value=1, required=False)


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


@extend_schema_view(
    list=extend_schema(summary='Тесты курсов', parameters=[OpenApiParameter('course', int), OpenApiParameter('lesson', int)]),
    retrieve=extend_schema(summary='Информация о тесте'),
    create=extend_schema(summary='Создать тест (преподаватель курса)'),
)
@extend_schema(tags=['tests'])
class TestViewSet(CourseScopedViewSet):
    queryset = Test.objects.select_related('course', 'lesson__section').order_by('-created_at')
    serializer_class = TestInfoSerializer
    filterset_fields = ['course', 'lesson', 'mode']

    def _managed_test(self):
        test = self.get_object()
        self.check_manage(test.course)
        return test

    @extend_schema(methods=['get'], summary='Вопросы теста с ответами (персонал)',
                   responses=TestQuestionManageSerializer(many=True))
    @extend_schema(methods=['post'], summary='Добавить вопрос из банка в тест', request=AddTestQuestionSerializer,
                   responses={201: TestQuestionManageSerializer})
    @action(detail=True, methods=['get', 'post'])
    def questions(self, request, pk=None):
        test = self._managed_test()
        if request.method == 'GET':
            items = test.test_questions.select_related('question__topic').prefetch_related('question__options')
            return Response(TestQuestionManageSerializer(items.order_by('order', 'id'), many=True,
                                                         context={'request': request}).data)

        serializer = AddTestQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = get_object_or_404(Question, id=serializer.validated_data['question_id'])
        tq = TestBuilderService.add_question(test, question, serializer.validated_data['points'],
                                             serializer.validated_data.get('order'))
        return Response(TestQuestionManageSerializer(tq, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @extend_schema(methods=['patch'], summary='Изменить баллы/порядок вопроса в тесте',
                   request=UpdateTestQuestionSerializer, responses=TestQuestionManageSerializer)
    @extend_schema(methods=['delete'], summary='Убрать вопрос из теста', responses={204: None})
    @action(detail=True, methods=['patch', 'delete'], url_path=r'questions/(?P<question_id>\d+)')
    def question_detail(self, request, pk=None, question_id=None):
        test = self._managed_test()
        tq = get_object_or_404(TestQuestion, test=test, question_id=question_id)
        TestBuilderService.ensure_editable(test)
        if request.method == 'DELETE':
            tq.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = UpdateTestQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for key, value in serializer.validated_data.items():
            setattr(tq, key, value)
        tq.save()
        return Response(TestQuestionManageSerializer(tq, context={'request': request}).data)

    @extend_schema(summary='Статистика теста: средний балл, процент сдачи, сложные вопросы',
                   responses={200: OpenApiResponse(description='Сводка по попыткам и вопросам')})
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        return Response(TestBuilderService.stats(self._managed_test()))
