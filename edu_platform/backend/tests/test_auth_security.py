import pyotp
import pytest

from apps.accounts.models import RefreshToken, TwoFactorSecret
from apps.accounts.services import decrypt_secret
from apps.organizations.models import Invite
from tests.conftest import PASSWORD


def login(api, email, **extra):
    return api.post('/api/v1/auth/login/', {'email': email, 'password': PASSWORD, **extra})


@pytest.mark.django_db
class TestJwtAndSessions:
    def test_login_token_is_accepted_by_protected_endpoints(self, api, make_user, org):
        make_user('s@a.kz', 'student', org)
        res = login(api, 's@a.kz')
        assert res.status_code == 200
        assert res.data['user']['org_id'] == org.id
        assert res.data['user']['roles'] == ['student']

        api.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access_token']}")
        me = api.get('/api/v1/auth/users/me/')
        assert me.status_code == 200
        assert me.data['email'] == 's@a.kz'
        assert me.data['roles'] == ['student']

    def test_refresh_keeps_organization(self, api, make_user, org):
        make_user('s@a.kz', 'student', org)
        refresh = login(api, 's@a.kz').data['refresh_token']
        res = api.post('/api/v1/auth/refresh/', {'refresh': refresh})
        assert res.status_code == 200
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access_token']}")
        assert api.get('/api/v1/auth/users/me/').data['roles'] == ['student']

    def test_refresh_without_token_is_401(self, api):
        assert api.post('/api/v1/auth/refresh/', {}).status_code == 401

    def test_change_password_invalidates_access_tokens(self, api, make_user):
        make_user('s@a.kz')
        access = login(api, 's@a.kz').data['access_token']
        api.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        res = api.post('/api/v1/auth/change-password/', {'old_password': PASSWORD, 'new_password': 'NewStrongPass456!'})
        assert res.status_code == 200
        assert api.get('/api/v1/auth/users/me/').status_code == 401

    def test_sessions_list_and_revoke(self, api, make_user):
        user = make_user('s@a.kz')
        access = login(api, 's@a.kz').data['access_token']
        api.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        sessions = api.get('/api/v1/auth/sessions/').data
        assert len(sessions) == 1 and sessions[0]['is_current'] is True

        res = api.delete(f"/api/v1/auth/sessions/{sessions[0]['id']}/")
        assert res.status_code == 200
        assert not RefreshToken.objects.filter(user=user, revoked_at__isnull=True).exists()
        assert api.delete(f"/api/v1/auth/sessions/{sessions[0]['id']}/").status_code == 404

    def test_logout_works_without_access_token(self, api, make_user):
        user = make_user('s@a.kz')
        refresh = login(api, 's@a.kz').data['refresh_token']
        fresh = type(api)()
        assert fresh.post('/api/v1/auth/logout/', {'refresh': refresh}).status_code == 200
        assert not RefreshToken.objects.filter(user=user, revoked_at__isnull=True).exists()

    def test_register_unknown_org_is_400(self, api):
        res = api.post('/api/v1/auth/register/', {
            'email': 'x@a.kz', 'password': PASSWORD, 'first_name': 'А', 'last_name': 'Б', 'org_slug': 'nope',
        })
        assert res.status_code == 400

    def test_verify_email_without_token_is_400(self, api):
        assert api.get('/api/v1/auth/verify-email/').status_code == 400

    def test_registration_sends_verification_email(self, api, org, django_capture_on_commit_callbacks):
        from django.core import mail
        # Письмо отправляется после коммита транзакции регистрации
        with django_capture_on_commit_callbacks(execute=True):
            res = api.post('/api/v1/auth/register/', {
                'email': 'new@a.kz', 'password': PASSWORD, 'first_name': 'А', 'last_name': 'Б', 'org_slug': org.slug,
            })
        assert res.status_code == 201
        assert len(mail.outbox) == 1
        assert '/api/v1/auth/verify-email/?token=' in mail.outbox[0].body


@pytest.mark.django_db
class TestTwoFactor:
    def _enable(self, api, user):
        access = login(api, user.email).data['access_token']
        api.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        setup = api.post('/api/v1/auth/2fa/setup/')
        assert setup.status_code == 200
        secret = setup.data['secret']
        # Секрет хранится зашифрованным
        assert TwoFactorSecret.objects.get(user=user).secret_encrypted != secret
        enable = api.post('/api/v1/auth/2fa/enable/', {'code': pyotp.TOTP(secret).now()})
        assert enable.status_code == 200
        api.credentials()
        return secret, enable.data['backup_codes']

    def test_login_requires_code_and_issues_no_tokens_before_it(self, api, make_user):
        user = make_user('s@a.kz')
        secret, _ = self._enable(api, user)

        res = login(api, 's@a.kz')
        assert res.status_code == 200
        assert res.data == {'requires_2fa': True}

        assert login(api, 's@a.kz', totp_code='000000').status_code == 401

        ok = login(api, 's@a.kz', totp_code=pyotp.TOTP(secret).now())
        assert ok.status_code == 200 and 'access_token' in ok.data

    def test_backup_code_works_once(self, api, make_user):
        user = make_user('s@a.kz')
        _, backup_codes = self._enable(api, user)
        assert login(api, 's@a.kz', totp_code=backup_codes[0]).status_code == 200
        assert login(api, 's@a.kz', totp_code=backup_codes[0]).status_code == 401

    def test_secret_roundtrip(self, api, make_user):
        user = make_user('s@a.kz')
        secret, _ = self._enable(api, user)
        assert decrypt_secret(TwoFactorSecret.objects.get(user=user).secret_encrypted) == secret


@pytest.mark.django_db
class TestInvites:
    def test_admin_invites_student_to_course(self, api, make_user, auth_client, org, course):
        admin = make_user('admin@a.kz', 'admin', org)
        res = auth_client(admin, org.id).post('/api/v1/orgs/invites/', {'role': 'student', 'course_id': course.id})
        assert res.status_code == 201
        token = res.data['invite_token']
        assert Invite.objects.get(id=res.data['id']).token_hash != token

        reg = api.post('/api/v1/auth/register-by-invite/', {
            'invite_token': token, 'email': 'pupil@a.kz', 'password': PASSWORD,
            'first_name': 'А', 'last_name': 'Б',
        })
        assert reg.status_code == 201
        assert reg.data['user']['email'] == 'pupil@a.kz'

        # Курс появился в «Мои курсы»
        my = auth_client(_user('pupil@a.kz'), org.id).get('/api/v1/courses/my/')
        assert [c['id'] for c in my.data['results']] == [course.id]

        # Одноразовое приглашение больше не работает
        again = api.post('/api/v1/auth/register-by-invite/', {
            'invite_token': token, 'email': 'other@a.kz', 'password': PASSWORD, 'first_name': 'А', 'last_name': 'Б',
        })
        assert again.status_code == 400

    def test_student_cannot_create_invites(self, make_user, auth_client, org):
        student = make_user('s@a.kz', 'student', org)
        res = auth_client(student, org.id).post('/api/v1/orgs/invites/', {'role': 'teacher'})
        assert res.status_code == 403


def _user(email):
    from django.contrib.auth import get_user_model
    return get_user_model().objects.get(email=email)
