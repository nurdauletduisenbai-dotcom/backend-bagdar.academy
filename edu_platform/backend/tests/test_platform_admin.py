from unittest import mock

import pytest

from apps.accounts.models import ParentStudentRelation
from apps.courses.models import Course, Enrollment
from apps.notifications.models import Notification
from apps.organizations.models import OrgMembership
from apps.payments.models import Order
from tests.conftest import PASSWORD


@pytest.fixture
def admin(make_user, org):
    return make_user('admin@a.kz', 'admin', org)


@pytest.fixture
def paid_course(org):
    return Course.objects.create(org=org, title='Платный', slug='paid', price='15000',
                                 status=Course.Status.PUBLISHED, access_days=30)


@pytest.mark.django_db
class TestPayments:
    def test_free_course_enrolls_immediately(self, make_user, auth_client, org, course):
        student = make_user('s@a.kz', 'student', org)
        res = auth_client(student, org.id).post('/api/v1/payments/orders/', {'course_id': course.id})
        assert res.status_code == 201 and res.data['status'] == 'paid'
        assert Enrollment.objects.filter(student=student, course=course, status='active').exists()

    def test_manual_payment_confirmed_by_admin_then_refunded(self, make_user, auth_client, org, admin, paid_course):
        student = make_user('s@a.kz', 'student', org)
        client = auth_client(student, org.id)
        order = client.post('/api/v1/payments/orders/', {'course_id': paid_course.id, 'provider': 'manual'},
                            HTTP_IDEMPOTENCY_KEY='key-1')
        assert order.status_code == 201 and order.data['status'] == 'pending'
        # Повторная отправка с тем же ключом не создаёт второй заказ
        again = client.post('/api/v1/payments/orders/', {'course_id': paid_course.id, 'provider': 'manual'},
                            HTTP_IDEMPOTENCY_KEY='key-1')
        assert again.data['id'] == order.data['id'] and Order.objects.count() == 1

        assert client.post(f"/api/v1/payments/orders/{order.data['id']}/mark-paid/").status_code == 403
        paid = auth_client(admin, org.id).post(f"/api/v1/payments/orders/{order.data['id']}/mark-paid/")
        assert paid.status_code == 200 and paid.data['status'] == 'paid'
        assert Enrollment.objects.get(student=student, course=paid_course).status == 'active'
        assert Notification.objects.filter(user=student, type='enrollment').exists()

        refund = auth_client(admin, org.id).post(f"/api/v1/payments/orders/{order.data['id']}/refund/")
        assert refund.status_code == 200 and refund.data['status'] == 'refunded'
        assert Enrollment.objects.get(student=student, course=paid_course).status == 'canceled'

    def test_kaspi_not_configured(self, make_user, auth_client, org, paid_course):
        student = make_user('s@a.kz', 'student', org)
        res = auth_client(student, org.id).post('/api/v1/payments/orders/',
                                                {'course_id': paid_course.id, 'provider': 'kaspi'})
        assert res.status_code == 400

    def test_stripe_webhook_marks_paid(self, api, make_user, org, paid_course, settings):
        settings.STRIPE_SECRET_KEY = 'sk_test_x'
        settings.STRIPE_WEBHOOK_SECRET = 'whsec_x'
        student = make_user('s@a.kz', 'student', org)
        order = Order.objects.create(user=student, course=paid_course, amount=15000, provider='stripe',
                                     idempotency_key='k', provider_ref='cs_test_1')
        event = {'type': 'checkout.session.completed',
                 'data': {'object': {'id': 'cs_test_1', 'payment_status': 'paid', 'metadata': {'order_id': str(order.id)}}}}
        with mock.patch('apps.payments.providers.StripeProvider.parse_webhook', return_value=event):
            res = api.post('/api/v1/payments/webhooks/stripe/', {}, HTTP_STRIPE_SIGNATURE='t=1,v1=x')
        assert res.status_code == 200
        order.refresh_from_db()
        assert order.status == 'paid'

        with mock.patch('apps.payments.providers.StripeProvider.parse_webhook', side_effect=ValueError('bad')):
            assert api.post('/api/v1/payments/webhooks/stripe/', {}).status_code == 400


@pytest.mark.django_db
class TestParentsAndProgress:
    def test_parent_link_and_child_progress(self, make_user, auth_client, org, course, enroll):
        student = make_user('s@a.kz', 'student', org)
        enroll(student, course)
        parent = make_user('p@a.kz', 'parent', org)
        parent_client = auth_client(parent, org.id)

        link = parent_client.post('/api/v1/parents/children/', {'student_email': 's@a.kz'})
        assert link.status_code == 201 and link.data['is_confirmed'] is False
        # До подтверждения прогресс ребёнка закрыт
        assert parent_client.get(f'/api/v1/progress/students/{student.id}/').status_code == 403

        confirm = auth_client(student, org.id).post(f"/api/v1/parents/requests/{link.data['id']}/")
        assert confirm.status_code == 200
        res = parent_client.get(f'/api/v1/progress/students/{student.id}/')
        assert res.status_code == 200 and res.data['courses'][0]['course_id'] == course.id

        report = parent_client.get(f'/api/v1/progress/courses/{course.id}/?student={student.id}')
        assert report.status_code == 200 and 'lessons' in report.data

    def test_stranger_cannot_see_progress(self, make_user, auth_client, org, other_org, course, enroll):
        student = make_user('s@a.kz', 'student', org)
        enroll(student, course)
        stranger = make_user('x@b.kz', 'parent', other_org)
        assert auth_client(stranger, other_org.id).get(f'/api/v1/progress/students/{student.id}/').status_code == 403

    def test_my_progress_and_org_summary(self, make_user, auth_client, org, course, enroll, admin):
        student = make_user('s@a.kz', 'student', org)
        enroll(student, course)
        assert auth_client(student, org.id).get('/api/v1/progress/my/').data[0]['course_id'] == course.id
        summary = auth_client(admin, org.id).get('/api/v1/progress/org/summary/')
        assert summary.status_code == 200 and summary.data['active_enrollments'] == 1
        assert auth_client(student, org.id).get('/api/v1/progress/org/summary/').status_code == 403

    def test_parent_relation_requires_same_org(self, make_user, auth_client, org, other_org):
        make_user('s@a.kz', 'student', org)
        parent = make_user('p@b.kz', 'parent', other_org)
        res = auth_client(parent, other_org.id).post('/api/v1/parents/children/', {'student_email': 's@a.kz'})
        assert res.status_code == 400
        assert not ParentStudentRelation.objects.exists()


@pytest.mark.django_db
class TestOrgManagement:
    def test_members_roles_and_audit(self, make_user, auth_client, org, admin):
        teacher = make_user('t@a.kz', 'teacher', org)
        client = auth_client(admin, org.id)
        members = client.get('/api/v1/orgs/members/')
        assert members.status_code == 200 and members.data['total'] == 2

        membership = OrgMembership.objects.get(user=teacher)
        res = client.patch(f'/api/v1/orgs/members/{membership.id}/', {'role': 'curator'})
        assert res.status_code == 200 and res.data['role'] == 'curator'

        logs = client.get('/api/v1/audit/logs/', {'action': 'role_change'})
        assert logs.status_code == 200 and logs.data['total'] == 1

    def test_cannot_remove_last_admin(self, auth_client, org, admin):
        membership = OrgMembership.objects.get(user=admin)
        res = auth_client(admin, org.id).delete(f'/api/v1/orgs/members/{membership.id}/')
        assert res.status_code == 400

    def test_teacher_cannot_change_roles(self, make_user, auth_client, org, admin):
        teacher = make_user('t@a.kz', 'teacher', org)
        membership = OrgMembership.objects.get(user=admin)
        res = auth_client(teacher, org.id).patch(f'/api/v1/orgs/members/{membership.id}/', {'role': 'student'})
        assert res.status_code == 403


@pytest.mark.django_db
class TestNotificationsAndAnnouncements:
    def test_course_announcement_and_inbox(self, make_user, auth_client, org, course, enroll, course_teacher):
        student = make_user('s@a.kz', 'student', org)
        enroll(student, course)
        res = auth_client(course_teacher, org.id).post(
            '/api/v1/announcements/', {'course': course.id, 'title': 'Контрольная в пятницу', 'content': 'Готовьтесь'})
        assert res.status_code == 201

        client = auth_client(student, org.id)
        assert client.get('/api/v1/notifications/unread-count/').data['unread'] == 1
        inbox = client.get('/api/v1/notifications/').data['results']
        assert client.post(f"/api/v1/notifications/{inbox[0]['id']}/read/").status_code == 200
        assert client.get('/api/v1/notifications/unread-count/').data['unread'] == 0
        assert client.get('/api/v1/announcements/').data['total'] == 1

    def test_student_cannot_post_org_announcement(self, make_user, auth_client, org):
        student = make_user('s@a.kz', 'student', org)
        res = auth_client(student, org.id).post('/api/v1/announcements/', {'title': 'x', 'content': 'y'})
        assert res.status_code == 403

    def test_preferences_disable_in_app(self, make_user, auth_client, org, course, enroll, course_teacher):
        student = make_user('s@a.kz', 'student', org)
        enroll(student, course)
        auth_client(student, org.id).patch('/api/v1/notifications/preferences/', {'in_app_enabled': False})
        auth_client(course_teacher, org.id).post(
            '/api/v1/announcements/', {'course': course.id, 'title': 'T', 'content': 'C'})
        assert not Notification.objects.filter(user=student).exists()


@pytest.mark.django_db
class TestPasswordReset:
    def test_reset_flow(self, api, make_user, django_capture_on_commit_callbacks):
        from django.core import mail
        make_user('s@a.kz')
        with django_capture_on_commit_callbacks(execute=True):
            assert api.post('/api/v1/auth/password-reset/', {'email': 's@a.kz'}).status_code == 200
        token = mail.outbox[0].body.split('token=')[1].split()[0]

        res = api.post('/api/v1/auth/password-reset/confirm/', {'token': token, 'new_password': 'BrandNewPass789!'})
        assert res.status_code == 200
        assert api.post('/api/v1/auth/login/', {'email': 's@a.kz', 'password': 'BrandNewPass789!'}).status_code == 200
        assert api.post('/api/v1/auth/login/', {'email': 's@a.kz', 'password': PASSWORD}).status_code == 401
        # Токен одноразовый
        again = api.post('/api/v1/auth/password-reset/confirm/', {'token': token, 'new_password': 'Another123Pass!'})
        assert again.status_code == 400

    def test_unknown_email_does_not_leak(self, api):
        assert api.post('/api/v1/auth/password-reset/', {'email': 'nobody@a.kz'}).status_code == 200
