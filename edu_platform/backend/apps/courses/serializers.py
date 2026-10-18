from rest_framework import serializers

from .models import Course


class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            'id',
            'title',
            'slug',
            'type',
            'subject',
            'grade_level',
            'price',
            'status',
            'is_free_preview_enabled',
            'created_at',
        )


class CourseDetailSerializer(serializers.ModelSerializer):
    sections = serializers.SerializerMethodField()

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
            'sections',
            'created_at',
        )

    def get_sections(self, obj):
        from apps.content.models import Section
        sections = Section.objects.filter(course=obj).prefetch_related('lessons')
        res = []
        for s in sections:
            lessons_data = []
            for lesson in s.lessons.all():
                lessons_data.append({
                    'id': lesson.id,
                    'title': lesson.title,
                    'order': lesson.order,
                    'is_free_preview': lesson.is_free_preview,
                    'is_published': lesson.is_published,
                    # Обратите внимание: youtube_video_id здесь НЕ отдается в целях безопасности!
                })
            res.append({
                'id': s.id,
                'title': s.title,
                'order': s.order,
                'lessons': lessons_data,
            })
        return res
