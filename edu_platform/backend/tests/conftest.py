from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.services import AuthService
from apps.courses.models import Course, CourseStaff, Enrollment
from apps.organizations.models import Organization, OrgMembership

User = get_user_model()
PASSWORD = 'StrongPassword123!'


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def org(db):
    return Organization.objects.create(name='Школа А', slug='school-a')


@pytest.fixture
def other_org(db):
    return Organization.objects.create(name='Школа Б', slug='school-b')


@pytest.fixture
def make_user(db):
    def _make(email, role=None, org=None, **extra):
        user = User.objects.create_user(email=email, password=PASSWORD, first_name='Имя', last_name='Фамилия',
                                        is_verified=True, **extra)
        if role and org:
            OrgMembership.objects.create(org=org, user=user, role=role)
        return user
    return _make


@pytest.fixture
def auth_client():
    """APIClient с access-токеном пользователя (как после логина)."""
    def _client(user, org_id=None, header_org=None):
        client = APIClient()
        token = AuthService.generate_jwt_access_token(user, org_id=org_id)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
        if header_org:
            headers['HTTP_X_ORG_ID'] = str(header_org)
        client.credentials(**headers)
        return client
    return _client


@pytest.fixture
def course(org):
    return Course.objects.create(org=org, title='Алгебра', slug='algebra', status=Course.Status.PUBLISHED)


@pytest.fixture
def enroll():
    def _enroll(student, course):
        return Enrollment.objects.create(
            course=course, student=student, status=Enrollment.Status.ACTIVE,
            access_until=timezone.now() + timedelta(days=30),
        )
    return _enroll


@pytest.fixture
def course_teacher(make_user, org, course):
    teacher = make_user('teacher@a.kz', 'teacher', org)
    CourseStaff.objects.create(course=course, teacher=teacher)
    return teacher
