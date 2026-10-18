from rest_framework import serializers

from apps.common.files import validate_upload
from apps.courses.models import Course

from .models import Comment, Lesson, Material, Section


class SectionSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    lessons_count = serializers.IntegerField(source='lessons.count', read_only=True)

    class Meta:
        model = Section
        fields = ('id', 'course', 'title', 'order', 'lessons_count', 'created_at')
        read_only_fields = ('id', 'created_at')


class LessonSerializer(serializers.ModelSerializer):
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())
    course_id = serializers.IntegerField(source='section.course_id', read_only=True)
    is_published = serializers.BooleanField(read_only=True)

    class Meta:
        model = Lesson
        fields = ('id', 'section', 'course_id', 'title', 'order', 'is_free_preview', 'publish_at', 'is_published',
                  'created_at')
        read_only_fields = ('id', 'created_at')


class MaterialSerializer(serializers.ModelSerializer):
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all())
    file = serializers.FileField(write_only=True, required=False, help_text='Загрузка файла (multipart)')
    has_file = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = ('id', 'lesson', 'title', 'file', 'file_url', 'file_type', 'file_size_bytes', 'order',
                  'has_file', 'download_url', 'created_at')
        read_only_fields = ('id', 'file_type', 'file_size_bytes', 'created_at')

    def get_has_file(self, obj) -> bool:
        return bool(obj.file)

    def get_download_url(self, obj) -> str | None:
        return f'/api/v1/materials/{obj.id}/download/' if obj.file else None

    def validate(self, attrs):
        file = validate_upload(attrs.get('file'))
        has_file = file or (self.instance and self.instance.file)
        has_url = attrs.get('file_url') or (self.instance and self.instance.file_url)
        if not has_file and not has_url:
            raise serializers.ValidationError('Загрузите файл или укажите ссылку file_url.')
        if file:
            attrs['file_size_bytes'] = file.size
            attrs['file_type'] = (file.name.rsplit('.', 1)[-1] if '.' in file.name else '').lower()
        return attrs


class LessonVideoBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    duration_seconds = serializers.IntegerField()
    order = serializers.IntegerField()
    is_completed = serializers.BooleanField()


class LessonDetailSerializer(LessonSerializer):
    videos = serializers.SerializerMethodField()
    materials = serializers.SerializerMethodField()
    assignments = serializers.SerializerMethodField()
    tests = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    has_access = serializers.SerializerMethodField()

    class Meta(LessonSerializer.Meta):
        fields = LessonSerializer.Meta.fields + ('has_access', 'is_completed', 'videos', 'materials',
                                                 'assignments', 'tests')

    def _user(self):
        return self.context['request'].user

    def get_has_access(self, obj) -> bool:
        return self.context.get('has_access', False)

    def get_is_completed(self, obj) -> bool:
        return obj.completions.filter(student=self._user()).exists()

    def get_videos(self, obj) -> list[dict]:
        from apps.videos.models import VideoProgress
        done = set(VideoProgress.objects.filter(video__lesson=obj, student=self._user(), is_completed=True)
                   .values_list('video_id', flat=True))
        return [
            {'id': v.id, 'title': v.title, 'duration_seconds': v.duration_seconds, 'order': v.order,
             'is_completed': v.id in done}
            for v in obj.videos.all()
        ]

    def get_materials(self, obj) -> list[dict]:
        if not self.context.get('has_access'):
            return []
        return MaterialSerializer(obj.materials.all(), many=True, context=self.context).data

    def get_assignments(self, obj) -> list[dict]:
        return [{'id': a.id, 'title': a.title, 'deadline': a.deadline} for a in obj.assignments.order_by('deadline')]

    def get_tests(self, obj) -> list[dict]:
        return [{'id': t.id, 'title': t.title, 'mode': t.mode} for t in obj.tests.order_by('id')]


class CommentSerializer(serializers.ModelSerializer):
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all())
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), required=False, allow_null=True)
    author = serializers.SerializerMethodField()
    replies_count = serializers.IntegerField(source='replies.count', read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'lesson', 'parent', 'author', 'content', 'is_hidden', 'replies_count', 'created_at',
                  'updated_at')
        read_only_fields = ('id', 'is_hidden', 'created_at', 'updated_at')

    def get_author(self, obj) -> dict:
        return {'id': obj.user_id, 'name': obj.user.get_full_name()}

    def validate(self, attrs):
        parent = attrs.get('parent')
        lesson = attrs.get('lesson') or (self.instance and self.instance.lesson)
        if parent and parent.lesson_id != lesson.id:
            raise serializers.ValidationError({'parent': 'Ответ должен относиться к тому же уроку.'})
        if self.instance and ('lesson' in attrs or 'parent' in attrs):
            if attrs.get('lesson', self.instance.lesson) != self.instance.lesson:
                raise serializers.ValidationError({'lesson': 'Нельзя перенести комментарий в другой урок.'})
        return attrs
