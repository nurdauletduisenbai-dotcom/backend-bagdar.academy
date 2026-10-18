from functools import reduce

from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.courses.access import can_manage_course, managed_course_ids, viewable_course_ids


class CourseScopedViewSet(viewsets.ModelViewSet):
    """
    Базовый ViewSet для объектов, принадлежащих курсу (разделы, уроки, задания, тесты, занятия...).

    - Чтение: только объекты курсов, которые пользователь может видеть (viewable_course_ids).
    - Создание/изменение/удаление: только тем, кто управляет курсом (can_manage_course).

    Наследник задаёт:
      course_path — путь ORM от модели до курса, например 'section__course';
      course_from_data(validated_data) — курс создаваемого объекта.
    """
    permission_classes = [permissions.IsAuthenticated]
    course_path = 'course'

    def base_queryset(self):
        return self.queryset

    def get_queryset(self):
        qs = self.base_queryset()
        if getattr(self, 'swagger_fake_view', False):
            return qs.none()
        org_id = getattr(self.request, 'org_id', None)
        qs = qs.filter(**{f'{self.course_path}__in': viewable_course_ids(self.request.user, org_id)})
        return self.filter_for_learner(qs)

    def filter_for_learner(self, qs):
        """Дополнительные ограничения для тех, кто не управляет курсом (например, неопубликованное)."""
        return qs

    def managed_ids(self):
        if not hasattr(self, '_managed_ids'):
            self._managed_ids = set(managed_course_ids(self.request.user))
        return self._managed_ids

    def course_of(self, obj):
        return reduce(getattr, self.course_path.split('__'), obj)

    def course_from_data(self, validated_data):
        return validated_data['course']

    def check_manage(self, course):
        if not can_manage_course(self.request.user, course):
            raise PermissionDenied('Изменять содержимое курса может администратор или преподаватель этого курса.')

    def perform_create(self, serializer):
        self.check_manage(self.course_from_data(serializer.validated_data))
        self.save_create(serializer)

    def save_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        self.check_manage(self.course_of(serializer.instance))
        # Перенос в другой курс/раздел — тоже только туда, где у пользователя есть права
        try:
            new_course = self.course_from_data({**self._current_values(serializer.instance),
                                                **serializer.validated_data})
        except (KeyError, AttributeError):
            new_course = None
        if new_course is not None:
            self.check_manage(new_course)
        serializer.save()

    def _current_values(self, instance):
        return {f.name: getattr(instance, f.name) for f in instance._meta.concrete_fields}

    def perform_destroy(self, instance):
        self.check_manage(self.course_of(instance))
        instance.delete()
