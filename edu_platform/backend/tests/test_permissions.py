from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.services import AuthService
from apps.content.models import Lesson, Section
from apps.courses.models import Course, Enrollment
from apps.organizations.models import Organization, OrgMembership
from apps.videos.models import Video

User = get_user_model()


@pytest.mark.django_db
class TestAccessAndTenantIsolation:
    def setup_method(self):
        self.client = APIClient()

        # Org 1 and Org 2
        self.org1 = Organization.objects.create(name='Школа №1', slug='school-1')
        self.org2 = Organization.objects.create(name='Лицей №2', slug='school-2')

        # Course in Org 1
        self.course_org1 = Course.objects.create(
            org=self.org1,
            title='Математика ОГЭ',
            slug='math-oge',
            status=Course.Status.PUBLISHED,
        )
        self.sec = Section.objects.create(course=self.course_org1, title='Введение')
        self.lesson_locked = Lesson.objects.create(section=self.sec, title='Закрытый урок', is_free_preview=False)
        self.lesson_preview = Lesson.objects.create(section=self.sec, title='Превью урок', is_free_preview=True)

        self.video_locked = Video.objects.create(
            lesson=self.lesson_locked,
            youtube_video_id='secretVid123',
            title='Секретное видео'
        )
        self.video_preview = Video.objects.create(
            lesson=self.lesson_preview,
            youtube_video_id='previewVid12',
            title='Превью видео'
        )

        # Student without enrollment
        self.student = User.objects.create_user(
            email='pupil@test.com',
            password='Password123!',
            first_name='Ученик',
            last_name='Тестов'
        )
        OrgMembership.objects.create(org=self.org1, user=self.student, role='student')
        self.token = AuthService.generate_jwt_access_token(self.student, org_id=self.org1.id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_student_without_enrollment_blocked_from_locked_video_403(self):
        """
        КРИТЕРИЙ ПРИЕМКИ 1:
        Ученик без активной записи на курс НЕ может получить доступ к видео (403 Forbidden).
        """
        res = self.client.get(f'/api/v1/videos/{self.video_locked.id}/play/')
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert 'Доступ к видео закрыт' in res.data['error']['message']

    def test_student_can_watch_free_preview_video(self):
        """Превью-уроки доступны без активной платной записи"""
        res = self.client.get(f'/api/v1/videos/{self.video_preview.id}/play/')
        assert res.status_code == status.HTTP_200_OK
        assert 'embed_url' in res.data
        assert 'youtube-nocookie.com' in res.data['embed_url']

    def test_student_with_active_enrollment_can_watch_locked_video(self):
        """После записи на курс ученик получает доступ"""
        Enrollment.objects.create(
            course=self.course_org1,
            student=self.student,
            status=Enrollment.Status.ACTIVE,
            access_until=timezone.now() + timedelta(days=30)
        )
        res = self.client.get(f'/api/v1/videos/{self.video_locked.id}/play/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['video_id'] == self.video_locked.id

    def test_tenant_isolation_cross_org_courses_invisible(self):
        """
        КРИТЕРИЙ ПРИЕМКИ 2:
        Пользователь одной организации не видит данные другой (изоляция по X-Org-ID).
        """
        # Создаем курс в Школе 2
        Course.objects.create(
            org=self.org2,
            title='Курс другой школы',
            slug='other-school-course',
            status=Course.Status.PUBLISHED,
        )

        # Запрос с заголовком X-Org-ID: school-1
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token}',
            HTTP_X_ORG_ID=str(self.org1.id)
        )
        res = self.client.get('/api/v1/courses/')
        assert res.status_code == status.HTTP_200_OK

        course_titles = [c['title'] for c in res.data['results']]
        assert 'Математика ОГЭ' in course_titles
        assert 'Курс другой школы' not in course_titles
