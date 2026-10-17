import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization, OrgMembership
from apps.courses.models import Course, Enrollment
from apps.questions.models import Topic, Question, QuestionOption
from apps.assessments.models import Test, TestQuestion, TestAttempt
from apps.accounts.services import AuthService

User = get_user_model()


@pytest.mark.django_db
class TestAssessmentEngine:
    def setup_method(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='Лицей', slug='lyceum')
        self.course = Course.objects.create(org=self.org, title='Геометрия', slug='geom', status=Course.Status.PUBLISHED)

        self.student = User.objects.create_user(
            email='pupil2@test.com',
            password='Password123!',
            first_name='Нурсултан',
            last_name='Тестов'
        )
        OrgMembership.objects.create(org=self.org, user=self.student, role='student')
        Enrollment.objects.create(
            course=self.course,
            student=self.student,
            status=Enrollment.Status.ACTIVE,
            access_until=timezone.now() + timedelta(days=30)
        )

        self.topic = Topic.objects.create(org=self.org, subject='Геометрия', name='Треугольники')

        # Вопрос 1: Single choice
        self.q1 = Question.objects.create(topic=self.topic, type='single', text='Сумма углов треугольника?', difficulty=1)
        self.opt1_corr = QuestionOption.objects.create(question=self.q1, text='180 градусов', is_correct=True)
        self.opt1_wrong = QuestionOption.objects.create(question=self.q1, text='360 градусов', is_correct=False)

        # Вопрос 2: Number with tolerance
        self.q2 = Question.objects.create(topic=self.topic, type='number', text='Длина гипотенузы катетов 3 и 4?', tolerance=0.1)
        QuestionOption.objects.create(question=self.q2, text='5.0', is_correct=True)

        # Тест
        self.test = Test.objects.create(
            course=self.course,
            title='Входной тест по геометрии',
            time_limit_minutes=15,
            passing_score_pct=50
        )
        TestQuestion.objects.create(test=self.test, question=self.q1, points=5.0)
        TestQuestion.objects.create(test=self.test, question=self.q2, points=5.0)

        self.token = AuthService.generate_jwt_access_token(self.student, org_id=self.org.id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_start_attempt_does_not_leak_correct_answers(self):
        """
        КРИТЕРИЙ ПРИЕМКИ 3:
        Клиент НЕ получает правильные ответы до сдачи теста.
        """
        res = self.client.post(f'/api/v1/tests/{self.test.id}/attempts/')
        assert res.status_code == status.HTTP_201_CREATED
        attempt_id = res.data['attempt_id']
        questions = res.data['questions']

        assert len(questions) == 2
        for q in questions:
            for opt in q['options']:
                assert 'is_correct' not in opt
                assert 'explanation' not in q

        # Автосохранение ответа
        save_res = self.client.put(
            f'/api/v1/tests/attempts/{attempt_id}/answers/{self.q1.id}/',
            {'selected_options': [self.opt1_corr.id]}
        )
        assert save_res.status_code == status.HTTP_200_OK

        # Сдача теста и автопроверка
        submit_res = self.client.post(f'/api/v1/tests/attempts/{attempt_id}/submit/')
        assert submit_res.status_code == status.HTTP_200_OK
        assert submit_res.data['score'] == 5.0
        assert submit_res.data['max_score'] == 10.0
        assert submit_res.data['score_pct'] == 50.0
        assert submit_res.data['is_passed'] is True
