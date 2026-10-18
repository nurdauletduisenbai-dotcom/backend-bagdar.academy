import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.content.models import Lesson, Section
from apps.notifications.models import Notification
from apps.progress.models import CourseProgress


@pytest.fixture
def lesson(course):
    section = Section.objects.create(course=course, title='Введение')
    return Lesson.objects.create(section=section, title='Урок 1')


@pytest.mark.django_db
class TestContentManagement:
    def test_teacher_builds_course_content(self, auth_client, org, course, course_teacher):
        client = auth_client(course_teacher, org.id)
        section = client.post('/api/v1/sections/', {'course': course.id, 'title': 'Глава 1'})
        assert section.status_code == 201
        lesson = client.post('/api/v1/lessons/', {'section': section.data['id'], 'title': 'Тригонометрия'})
        assert lesson.status_code == 201
        video = client.post('/api/v1/videos/', {'lesson': lesson.data['id'], 'title': 'Лекция',
                                                'youtube_url': 'https://youtu.be/dQw4w9WgXcQ', 'duration_seconds': 300})
        assert video.status_code == 201
        assert video.data['youtube_video_id'] == 'dQw4w9WgXcQ'

    def test_student_cannot_edit_content(self, make_user, auth_client, org, course, enroll):
        student = make_user('s@a.kz', 'student', org)
        enroll(student, course)
        res = auth_client(student, org.id).post('/api/v1/sections/', {'course': course.id, 'title': 'Взлом'})
        assert res.status_code == 403

    def test_teacher_of_other_course_cannot_edit(self, make_user, auth_client, org, course):
        stranger = make_user('t2@a.kz', 'teacher', org)
        res = auth_client(stranger, org.id).post('/api/v1/sections/', {'course': course.id, 'title': 'Чужой'})
        assert res.status_code == 403

    def test_material_upload_and_protected_download(self, make_user, auth_client, org, course, course_teacher,
                                                    enroll, lesson):
        teacher = auth_client(course_teacher, org.id)
        upload = SimpleUploadedFile('конспект.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        res = teacher.post('/api/v1/materials/', {'lesson': lesson.id, 'title': 'Конспект', 'file': upload},
                           format='multipart')
        assert res.status_code == 201, res.data
        material_id = res.data['id']
        assert res.data['download_url'] == f'/api/v1/materials/{material_id}/download/'

        student = make_user('s@a.kz', 'student', org)
        enroll(student, course)
        download = auth_client(student, org.id).get(f'/api/v1/materials/{material_id}/download/')
        assert download.status_code == 200
        assert b''.join(download.streaming_content) == b'%PDF-1.4 test'

        outsider = make_user('o@a.kz', 'student', org)
        assert auth_client(outsider, org.id).get(f'/api/v1/materials/{material_id}/download/').status_code == 404

    def test_upload_rejects_bad_extension(self, auth_client, org, course_teacher, lesson):
        bad = SimpleUploadedFile('virus.exe', b'MZ', content_type='application/octet-stream')
        res = auth_client(course_teacher, org.id).post(
            '/api/v1/materials/', {'lesson': lesson.id, 'title': 'x', 'file': bad}, format='multipart')
        assert res.status_code == 400

    def test_lesson_detail_and_completion_updates_progress(self, make_user, auth_client, org, course, enroll, lesson):
        student = make_user('s@a.kz', 'student', org)
        enroll(student, course)
        client = auth_client(student, org.id)
        detail = client.get(f'/api/v1/lessons/{lesson.id}/')
        assert detail.status_code == 200 and detail.data['has_access'] is True
        assert client.post(f'/api/v1/lessons/{lesson.id}/complete/').status_code == 200
        progress = CourseProgress.objects.get(enrollment__student=student)
        assert progress.percent_completed == 100.0

    def test_free_preview_lesson_open_without_enrollment(self, make_user, auth_client, org, lesson):
        lesson.is_free_preview = True
        lesson.save()
        outsider = make_user('o@a.kz', 'student', org)
        res = auth_client(outsider, org.id).get(f'/api/v1/lessons/{lesson.id}/')
        assert res.status_code == 200
        assert res.data['has_access'] is False and res.data['materials'] == []

    def test_comment_reply_notifies_author(self, make_user, auth_client, org, course, enroll, lesson,
                                           course_teacher):
        student = make_user('s@a.kz', 'student', org)
        enroll(student, course)
        question = auth_client(student, org.id).post('/api/v1/comments/', {'lesson': lesson.id, 'content': 'Вопрос?'})
        assert question.status_code == 201
        reply = auth_client(course_teacher, org.id).post(
            '/api/v1/comments/', {'lesson': lesson.id, 'parent': question.data['id'], 'content': 'Ответ'})
        assert reply.status_code == 201
        assert Notification.objects.filter(user=student, type='comment_reply').exists()


@pytest.mark.django_db
class TestQuestionBank:
    def test_teacher_creates_question_with_validation(self, make_user, auth_client, org):
        teacher = make_user('t@a.kz', 'teacher', org)
        client = auth_client(teacher, org.id)
        topic = client.post('/api/v1/topics/', {'subject': 'Математика', 'name': 'Дроби'})
        assert topic.status_code == 201

        bad = client.post('/api/v1/questions/', {
            'topic': topic.data['id'], 'type': 'single', 'text': '1/2 + 1/2?',
            'options': [{'text': '1', 'is_correct': True}, {'text': '2', 'is_correct': True}],
        })
        assert bad.status_code == 400

        ok = client.post('/api/v1/questions/', {
            'topic': topic.data['id'], 'type': 'single', 'text': '1/2 + 1/2?',
            'options': [{'text': '1', 'is_correct': True}, {'text': '2'}],
        })
        assert ok.status_code == 201
        assert len(ok.data['options']) == 2

    def test_student_has_no_access_to_bank(self, make_user, auth_client, org):
        student = make_user('s@a.kz', 'student', org)
        assert auth_client(student, org.id).get('/api/v1/questions/').status_code == 403

    def test_bank_requires_org(self, make_user, auth_client, org, other_org):
        from apps.organizations.models import OrgMembership
        teacher = make_user('t@a.kz', 'teacher', org)
        OrgMembership.objects.create(org=other_org, user=teacher, role='teacher')
        assert auth_client(teacher).get('/api/v1/questions/').status_code == 400
