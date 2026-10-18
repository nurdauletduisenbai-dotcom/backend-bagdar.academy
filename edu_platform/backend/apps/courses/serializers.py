import uuid

from django.utils import timezone
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.common.permissions import STAFF_ROLES

from .models import Course, Enrollment


class CourseListSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True, help_text='Если пусто — генерируется из названия')

    class Meta:
        model = Course
        fields = (
            'id',
            'title',
            'slug',
            'description',
            'type',
            'subject',
            'grade_level',
            'price',
            'status',
            'is_free_preview_enabled',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')
        extra_kwargs = {'description': {'write_only': True, 'required': False}}

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Цена не может быть отрицательной.')
        return value

    def validate(self, attrs):
        org_id = self.context['request'].org_id
        slug = attrs.get('slug')
        if 'title' in attrs and not slug and not (self.instance and self.instance.slug):
            slug = f"{slugify(attrs['title'], allow_unicode=True)[:200] or 'course'}-{uuid.uuid4().hex[:6]}"
            attrs['slug'] = slug
        if slug:
            clash = Course.all_objects.filter(org_id=org_id, slug=slug)
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError({'slug': 'Курс с таким slug уже есть в организации.'})
        return attrs


class LessonVideoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    duration_seconds = serializers.IntegerField()


class CourseLessonSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    order = serializers.IntegerField()
    is_free_preview = serializers.BooleanField()
    is_published = serializers.BooleanField()
    videos = LessonVideoSerializer(many=True, help_text='youtube_video_id не отдаётся: смотреть через /videos/{id}/play/')


class CourseSectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    order = serializers.IntegerField()
    lessons = CourseLessonSerializer(many=True)


class CourseTestBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    mode = serializers.CharField()
    time_limit_minutes = serializers.IntegerField()
    max_attempts = serializers.IntegerField()
    lesson_id = serializers.IntegerField(allow_null=True)


class CourseDetailSerializer(CourseListSerializer):
    sections = serializers.SerializerMethodField()
    tests = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ('sections', 'tests', 'is_enrolled')
        extra_kwargs = {}

    def _is_staff(self, obj) -> bool:
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return any(r in STAFF_ROLES for r in user.get_roles_for_org(obj.org_id))

    @extend_schema_field(CourseSectionSerializer(many=True))
    def get_sections(self, obj):
        from apps.content.models import Section
        show_all = self._is_staff(obj)
        sections = Section.objects.filter(course=obj).prefetch_related('lessons__videos')
        result = []
        for section in sections:
            lessons = []
            for lesson in section.lessons.all():
                if not show_all and not lesson.is_published:
                    continue
                lessons.append({
                    'id': lesson.id,
                    'title': lesson.title,
                    'order': lesson.order,
                    'is_free_preview': lesson.is_free_preview,
                    'is_published': lesson.is_published,
                    # youtube_video_id намеренно НЕ отдаётся — только через защищённый /play/
                    'videos': [
                        {'id': v.id, 'title': v.title, 'duration_seconds': v.duration_seconds}
                        for v in lesson.videos.all()
                    ],
                })
            result.append({'id': section.id, 'title': section.title, 'order': section.order, 'lessons': lessons})
        return result

    @extend_schema_field(CourseTestBriefSerializer(many=True))
    def get_tests(self, obj):
        now = timezone.now()
        tests = obj.tests.all().order_by('id')
        if not self._is_staff(obj):
            tests = [t for t in tests if not t.available_to or t.available_to >= now]
        return [
            {
                'id': t.id,
                'title': t.title,
                'mode': t.mode,
                'time_limit_minutes': t.time_limit_minutes,
                'max_attempts': t.max_attempts,
                'lesson_id': t.lesson_id,
            }
            for t in tests
        ]

    def get_is_enrolled(self, obj) -> bool:
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return Enrollment.objects.filter(
            course=obj, student=user, status=Enrollment.Status.ACTIVE, access_until__gte=timezone.now()
        ).exists()


class EnrollStudentSerializer(serializers.Serializer):
    student_email = serializers.EmailField()
    access_days = serializers.IntegerField(min_value=1, max_value=3650, default=365)
    group_id = serializers.IntegerField(required=False, allow_null=True)


class EnrollmentSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source='student.email', read_only=True)

    class Meta:
        model = Enrollment
        fields = ('id', 'course', 'group', 'student', 'student_email', 'status', 'access_until', 'enrolled_at')
        read_only_fields = fields
