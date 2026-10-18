from datetime import timedelta

import pytest
from django.utils import timezone

from apps.content.models import Lesson, Section
from apps.courses.models import Course, CourseStaff
from apps.organizations.models import OrgMembership
from apps.videos.models import Video, VideoProgress


@pytest.mark.django_db
class TestTenantIsolation:
    def test_header_for_foreign_org_is_forbidden(self, make_user, auth_client, org, other_org):
        teacher = make_user('t@a.kz', 'teacher', org)
        res = auth_client(teacher, org.id, header_org=other_org.id).get('/api/v1/courses/')
        assert res.status_code == 403

    def test_roles_do_not_leak_between_orgs(self, make_user, auth_client, org, other_org):
        """Учитель школы А, который в школе Б только ученик, не может создавать курсы в Б."""
        user = make_user('t@a.kz', 'teacher', org)
        OrgMembership.objects.create(org=other_org, user=user, role='student')
        res = auth_client(user, header_org=other_org.id).post('/api/v1/courses/', {'title': 'Взлом'})
        assert res.status_code == 403

    def test_multi_org_user_without_header_has_no_roles(self, make_user, auth_client, org, other_org):
        user = make_user('t@a.kz', 'teacher', org)
        OrgMembership.objects.create(org=other_org, user=user, role='teacher')
        res = auth_client(user).post('/api/v1/courses/', {'title': 'Без организации'})
        assert res.status_code == 403

    def test_foreign_course_detail_is_404(self, make_user, auth_client, org, other_org):
        foreign = Course.objects.create(org=other_org, title='Чужой', slug='foreign', status=Course.Status.PUBLISHED)
        student = make_user('s@a.kz', 'student', org)
        res = auth_client(student, org.id, header_org=org.id).get(f'/api/v1/courses/{foreign.id}/')
        assert res.status_code == 404


@pytest.mark.django_db
class TestCoursePermissions:
    def test_guest_sees_published_catalog_only(self, api, org, course):
        Course.objects.create(org=org, title='Черновик', slug='draft')
        res = api.get('/api/v1/courses/', HTTP_X_ORG_ID=str(org.id))
        assert res.status_code == 200
        assert [c['title'] for c in res.data['results']] == ['Алгебра']

    def test_student_cannot_create_or_delete(self, make_user, auth_client, org, course):
        student = make_user('s@a.kz', 'student', org)
        client = auth_client(student, org.id)
        assert client.post('/api/v1/courses/', {'title': 'Мой курс'}).status_code == 403
        assert client.delete(f'/api/v1/courses/{course.id}/').status_code == 403

    def test_teacher_creates_course_and_becomes_staff(self, make_user, auth_client, org):
        teacher = make_user('t@a.kz', 'teacher', org)
        res = auth_client(teacher, org.id).post('/api/v1/courses/', {'title': 'Физика 9', 'price': '0'})
        assert res.status_code == 201
        course = Course.objects.get(id=res.data['id'])
        assert course.org_id == org.id and course.slug
        assert CourseStaff.objects.filter(course=course, teacher=teacher).exists()

    def test_teacher_cannot_edit_someone_elses_course(self, make_user, auth_client, org, course):
        other_teacher = make_user('t2@a.kz', 'teacher', org)
        res = auth_client(other_teacher, org.id).patch(f'/api/v1/courses/{course.id}/', {'title': 'Чужой'})
        assert res.status_code == 403

    def test_course_teacher_edits_and_soft_deletes(self, auth_client, org, course, course_teacher):
        client = auth_client(course_teacher, org.id)
        assert client.patch(f'/api/v1/courses/{course.id}/', {'title': 'Алгебра 10'}).status_code == 200
        assert client.delete(f'/api/v1/courses/{course.id}/').status_code == 204
        assert Course.all_objects.get(id=course.id).deleted_at is not None

    def test_staff_enrolls_student(self, make_user, auth_client, org, course, course_teacher):
        make_user('s@a.kz', 'student', org)
        res = auth_client(course_teacher, org.id).post(
            f'/api/v1/courses/{course.id}/enroll-student/', {'student_email': 's@a.kz'}
        )
        assert res.status_code == 201

    def test_detail_hides_unpublished_lessons_and_youtube_ids(self, make_user, auth_client, org, course):
        section = Section.objects.create(course=course, title='Раздел')
        Lesson.objects.create(section=section, title='Готов')
        Lesson.objects.create(section=section, title='Завтра', publish_at=timezone.now() + timedelta(days=1))
        lesson = section.lessons.get(title='Готов')
        Video.objects.create(lesson=lesson, youtube_video_id='abcdefghijk', title='Видео')

        student = make_user('s@a.kz', 'student', org)
        res = auth_client(student, org.id).get(f'/api/v1/courses/{course.id}/')
        lessons = res.data['sections'][0]['lessons']
        assert [lesson['title'] for lesson in lessons] == ['Готов']
        assert 'abcdefghijk' not in str(res.data)
        assert lessons[0]['videos'][0]['title'] == 'Видео'


@pytest.mark.django_db
class TestVideos:
    def _video(self, course, duration=600, preview=False):
        section = Section.objects.create(course=course, title='Раздел')
        lesson = Lesson.objects.create(section=section, title='Урок', is_free_preview=preview)
        return Video.objects.create(lesson=lesson, youtube_video_id='abcdefghijk', title='Видео',
                                    duration_seconds=duration)

    def test_missing_video_is_404(self, make_user, auth_client, org):
        student = make_user('s@a.kz', 'student', org)
        assert auth_client(student, org.id).get('/api/v1/videos/999999/play/').status_code == 404

    def test_teacher_of_other_org_cannot_watch(self, make_user, auth_client, org, other_org, course):
        video = self._video(course)
        stranger = make_user('t@b.kz', 'teacher', other_org)
        assert auth_client(stranger, other_org.id).get(f'/api/v1/videos/{video.id}/play/').status_code == 403

    def test_progress_cannot_jump_to_the_end(self, make_user, auth_client, org, course, enroll):
        video = self._video(course, duration=600)
        student = make_user('s@a.kz', 'student', org)
        enroll(student, course)
        client = auth_client(student, org.id)
        assert client.get(f'/api/v1/videos/{video.id}/play/').status_code == 200

        res = client.put(f'/api/v1/videos/{video.id}/progress/', {'watched_seconds': 600})
        assert res.status_code == 200
        assert res.data['is_completed'] is False
        assert res.data['watched_seconds'] < 60

        # Спустя реальное время прогресс засчитывается
        VideoProgress.objects.filter(video=video).update(last_watched_at=timezone.now() - timedelta(minutes=10))
        res = client.put(f'/api/v1/videos/{video.id}/progress/', {'watched_seconds': 600})
        assert res.data['is_completed'] is True

    def test_invalid_progress_is_400(self, make_user, auth_client, org, course, enroll):
        video = self._video(course)
        student = make_user('s@a.kz', 'student', org)
        enroll(student, course)
        res = auth_client(student, org.id).put(f'/api/v1/videos/{video.id}/progress/', {'watched_seconds': 'abc'})
        assert res.status_code == 400
