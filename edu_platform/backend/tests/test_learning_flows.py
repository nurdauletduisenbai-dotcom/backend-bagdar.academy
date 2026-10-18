from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.accounts.models import ParentStudentRelation
from apps.assessments.models import Test, TestQuestion
from apps.assignments.models import Assignment
from apps.assignments.services import AssignmentService
from apps.content.models import Lesson, Section
from apps.courses.models import Group
from apps.notifications.models import Notification
from apps.questions.models import Question, QuestionOption, Topic
from apps.schedule.models import Session
from apps.schedule.services import ScheduleService


@pytest.fixture
def lesson(course):
    section = Section.objects.create(course=course, title='Раздел')
    return Lesson.objects.create(section=section, title='Урок')


@pytest.fixture
def student(make_user, org, course, enroll):
    user = make_user('s@a.kz', 'student', org)
    enroll(user, course)
    return user


@pytest.mark.django_db
class TestAssignments:
    def test_full_cycle(self, auth_client, org, lesson, course_teacher, student):
        teacher = auth_client(course_teacher, org.id)
        created = teacher.post('/api/v1/assignments/', {
            'lesson': lesson.id, 'title': 'ДЗ 1', 'description': 'Решить задачи',
            'deadline': (timezone.now() + timedelta(days=2)).isoformat(), 'max_score': 10,
        })
        assert created.status_code == 201
        assert Notification.objects.filter(user=student, type='assignment_new').exists()

        client = auth_client(student, org.id)
        upload = SimpleUploadedFile('решение.pdf', b'%PDF', content_type='application/pdf')
        submit = client.post(f"/api/v1/assignments/{created.data['id']}/submit/",
                             {'text_content': 'Готово', 'file': upload}, format='multipart')
        assert submit.status_code == 201, submit.data
        assert submit.data['is_late'] is False

        grade = teacher.post(f"/api/v1/submissions/{submit.data['id']}/grade/", {'score': 9, 'feedback': 'Отлично'})
        assert grade.status_code == 200 and grade.data['status'] == 'graded'
        assert Notification.objects.filter(user=student, type='assignment_graded').exists()

        # Проверенную работу без разрешения пересдать нельзя
        again = client.post(f"/api/v1/assignments/{created.data['id']}/submit/", {'text_content': 'v2'})
        assert again.status_code == 400

        # Ученик не может сам себе поставить оценку
        assert client.post(f"/api/v1/submissions/{submit.data['id']}/grade/", {'score': 10}).status_code == 403

    def test_late_submission_rules(self, auth_client, org, lesson, student):
        assignment = Assignment.objects.create(lesson=lesson, title='Старое', description='-',
                                               deadline=timezone.now() - timedelta(hours=1))
        client = auth_client(student, org.id)
        late = client.post(f'/api/v1/assignments/{assignment.id}/submit/', {'text_content': 'поздно'})
        assert late.status_code == 201 and late.data['is_late'] is True

        # Если задание не принимает опоздания — новая сдача после дедлайна отклоняется
        assignment.accept_late = False
        assignment.save()
        assignment.submissions.all().delete()
        assert client.post(f'/api/v1/assignments/{assignment.id}/submit/', {'text_content': 'x'}).status_code == 400

    def test_parent_sees_child_submission(self, make_user, auth_client, org, lesson, student):
        assignment = Assignment.objects.create(lesson=lesson, title='ДЗ', description='-',
                                               deadline=timezone.now() + timedelta(days=1))
        AssignmentService.submit(assignment, student, text_content='ответ')
        parent = make_user('p@a.kz', 'parent', org)
        ParentStudentRelation.objects.create(parent=parent, student=student, is_confirmed=True)
        res = auth_client(parent, org.id).get('/api/v1/submissions/')
        assert res.status_code == 200 and res.data['total'] == 1

    def test_deadline_reminders_sent_once(self, lesson, student):
        Assignment.objects.create(lesson=lesson, title='Скоро', description='-',
                                  deadline=timezone.now() + timedelta(hours=3))
        assert AssignmentService.send_deadline_reminders() == 1
        assert AssignmentService.send_deadline_reminders() == 0


@pytest.mark.django_db
class TestSchedule:
    def test_sessions_attendance_and_visibility(self, auth_client, org, course, course_teacher, student):
        group = Group.objects.create(course=course, name='10А')
        from apps.courses.models import Enrollment
        Enrollment.objects.filter(student=student).update(group=group)

        teacher = auth_client(course_teacher, org.id)
        start = timezone.now() + timedelta(days=1)
        payload = {'group': group.id, 'title': 'Урок 1', 'start_time': start.isoformat(),
                   'end_time': (start + timedelta(hours=1)).isoformat()}
        created = teacher.post('/api/v1/sessions/', payload)
        assert created.status_code == 201
        assert teacher.post('/api/v1/sessions/', payload).status_code == 400  # пересечение

        marked = teacher.put(f"/api/v1/sessions/{created.data['id']}/attendance/",
                             {'records': [{'student_id': student.id, 'status': 'late'}]})
        assert marked.status_code == 200 and marked.data[0]['status'] == 'late'

        client = auth_client(student, org.id)
        assert [s['id'] for s in client.get('/api/v1/sessions/').data['results']] == [created.data['id']]
        assert client.get('/api/v1/attendance/').data['results'][0]['status'] == 'late'

    def test_session_reminder(self, course, student):
        group = Group.objects.create(course=course, name='Б')
        from apps.courses.models import Enrollment
        Enrollment.objects.filter(student=student).update(group=group)
        start = timezone.now() + timedelta(minutes=10)
        Session.objects.create(group=group, title='Скоро', start_time=start, end_time=start + timedelta(hours=1))
        assert ScheduleService.send_session_reminders() == 1
        assert ScheduleService.send_session_reminders() == 0


@pytest.mark.django_db
class TestTestBuilder:
    def test_builder_and_stats(self, auth_client, org, course, course_teacher, student):
        teacher = auth_client(course_teacher, org.id)
        test = teacher.post('/api/v1/tests/', {'course': course.id, 'title': 'Квиз', 'time_limit_minutes': 10})
        assert test.status_code == 201
        topic = Topic.objects.create(org=org, subject='М', name='Т')
        q = Question.objects.create(topic=topic, type='single', text='?')
        right = QuestionOption.objects.create(question=q, text='да', is_correct=True)
        QuestionOption.objects.create(question=q, text='нет')

        added = teacher.post(f"/api/v1/tests/{test.data['id']}/questions/", {'question_id': q.id, 'points': 2})
        assert added.status_code == 201

        client = auth_client(student, org.id)
        attempt = client.post(f"/api/v1/tests/{test.data['id']}/attempts/").data
        client.put(f"/api/v1/tests/attempts/{attempt['attempt_id']}/answers/{q.id}/", {'selected_options': [right.id]})
        client.post(f"/api/v1/tests/attempts/{attempt['attempt_id']}/submit/")

        stats = teacher.get(f"/api/v1/tests/{test.data['id']}/stats/")
        assert stats.status_code == 200
        assert stats.data['attempts'] == 1 and stats.data['pass_rate_pct'] == 100.0
        assert Notification.objects.filter(user=student, type='test_result').exists()

        # После сданных попыток состав теста менять нельзя
        q2 = Question.objects.create(topic=topic, type='open', text='Эссе')
        assert teacher.post(f"/api/v1/tests/{test.data['id']}/questions/", {'question_id': q2.id}).status_code == 400

        # Ученику конструктор недоступен
        assert client.get(f"/api/v1/tests/{test.data['id']}/questions/").status_code == 403

    def test_foreign_org_question_rejected(self, auth_client, org, other_org, course, course_teacher):
        test = Test.objects.create(course=course, title='Т')
        foreign_topic = Topic.objects.create(org=other_org, subject='X', name='Y')
        q = Question.objects.create(topic=foreign_topic, type='open', text='?')
        res = auth_client(course_teacher, org.id).post(f'/api/v1/tests/{test.id}/questions/', {'question_id': q.id})
        assert res.status_code == 400
        assert not TestQuestion.objects.filter(test=test).exists()
