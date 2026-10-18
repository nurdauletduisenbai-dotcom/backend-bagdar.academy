from datetime import timedelta

import pytest
from django.utils import timezone

from apps.assessments.models import Test, TestAttempt, TestQuestion
from apps.questions.models import Question, QuestionOption, Topic


@pytest.fixture
def setup(make_user, auth_client, org, course, enroll):
    student = make_user('s@a.kz', 'student', org)
    enroll(student, course)
    topic = Topic.objects.create(org=org, subject='Математика', name='Общее')

    single = Question.objects.create(topic=topic, type='single', text='2+2?')
    right = QuestionOption.objects.create(question=single, text='4', is_correct=True)
    QuestionOption.objects.create(question=single, text='5')

    short = Question.objects.create(topic=topic, type='short', text='Столица Казахстана?')
    QuestionOption.objects.create(question=short, text='Астана', is_correct=True)

    match = Question.objects.create(topic=topic, type='match', text='Сопоставьте')
    m1 = QuestionOption.objects.create(question=match, text='H2O', match_target='Вода')
    m2 = QuestionOption.objects.create(question=match, text='NaCl', match_target='Соль')

    test = Test.objects.create(course=course, title='Контрольная', time_limit_minutes=10, passing_score_pct=50)
    for q in (single, short, match):
        TestQuestion.objects.create(test=test, question=q, points=1)

    return {
        'client': auth_client(student, org.id), 'student': student, 'test': test, 'topic': topic,
        'single': single, 'right': right, 'short': short, 'match': match, 'm1': m1, 'm2': m2,
    }


def start(ctx):
    res = ctx['client'].post(f"/api/v1/tests/{ctx['test'].id}/attempts/")
    assert res.status_code == 201, res.data
    return res.data


def answer(ctx, attempt_id, question, **payload):
    return ctx['client'].put(f'/api/v1/tests/attempts/{attempt_id}/answers/{question.id}/', payload)


@pytest.mark.django_db
class TestAssessmentRules:
    def test_correct_answers_are_not_leaked(self, setup):
        data = start(setup)
        by_id = {q['id']: q for q in data['questions']}
        assert by_id[setup['short'].id]['options'] == []  # «Астана» не уходит клиенту
        match_q = by_id[setup['match'].id]
        assert all('match_target' not in o for o in match_q['options'])
        assert sorted(match_q['match_targets']) == ['Вода', 'Соль']
        assert 'Астана' not in str(data)

    def test_resume_keeps_question_order(self, setup):
        setup['test'].shuffle_questions = True
        setup['test'].save()
        first = start(setup)
        second = start(setup)
        assert first['attempt_id'] == second['attempt_id']
        assert [q['id'] for q in first['questions']] == [q['id'] for q in second['questions']]

    def test_foreign_question_is_rejected(self, setup):
        foreign = Question.objects.create(topic=setup['topic'], type='single', text='Чужой')
        opt = QuestionOption.objects.create(question=foreign, text='да', is_correct=True)
        attempt_id = start(setup)['attempt_id']
        assert answer(setup, attempt_id, foreign, selected_options=[opt.id]).status_code == 404

    def test_option_from_other_question_is_rejected(self, setup):
        attempt_id = start(setup)['attempt_id']
        res = answer(setup, attempt_id, setup['single'], selected_options=[setup['m1'].id])
        assert res.status_code == 400

    def test_full_grading_including_match(self, setup):
        attempt_id = start(setup)['attempt_id']
        assert answer(setup, attempt_id, setup['single'], selected_options=[setup['right'].id]).status_code == 200
        assert answer(setup, attempt_id, setup['short'], text_answer='  астана ').status_code == 200
        res = answer(setup, attempt_id, setup['match'],
                     selected_options={str(setup['m1'].id): 'Вода', str(setup['m2'].id): 'Соль'})
        assert res.status_code == 200

        result = setup['client'].post(f'/api/v1/tests/attempts/{attempt_id}/submit/')
        assert result.status_code == 200
        assert result.data['status'] == 'graded'
        assert result.data['score'] == 3.0 and result.data['score_pct'] == 100.0
        assert result.data['review'] is not None  # show_answers_after_submit=True

    def test_answers_after_deadline_are_rejected(self, setup):
        attempt_id = start(setup)['attempt_id']
        TestAttempt.objects.filter(id=attempt_id).update(started_at=timezone.now() - timedelta(minutes=30))
        res = answer(setup, attempt_id, setup['single'], selected_options=[setup['right'].id])
        assert res.status_code == 400
        assert TestAttempt.objects.get(id=attempt_id).status == TestAttempt.Status.EXPIRED

    def test_max_attempts_enforced(self, setup):
        setup['test'].max_attempts = 1
        setup['test'].save()
        attempt_id = start(setup)['attempt_id']
        setup['client'].post(f'/api/v1/tests/attempts/{attempt_id}/submit/')
        res = setup['client'].post(f"/api/v1/tests/{setup['test'].id}/attempts/")
        assert res.status_code == 400

    def test_open_question_waits_for_teacher(self, setup, make_user, auth_client, org, course):
        open_q = Question.objects.create(topic=setup['topic'], type='open', text='Докажите теорему')
        TestQuestion.objects.create(test=setup['test'], question=open_q, points=5)
        attempt_id = start(setup)['attempt_id']
        answer(setup, attempt_id, open_q, text_answer='Доказательство...')
        submitted = setup['client'].post(f'/api/v1/tests/attempts/{attempt_id}/submit/')
        assert submitted.data['status'] == 'submitted'

        # Ученик не может сам себе поставить балл
        grade_url = f'/api/v1/tests/attempts/{attempt_id}/answers/{open_q.id}/grade/'
        assert setup['client'].put(grade_url, {'score': 5}).status_code == 403

        teacher = make_user('t@a.kz', 'teacher', org)
        graded = auth_client(teacher, org.id).put(grade_url, {'score': 4, 'feedback': 'Хорошо'})
        assert graded.status_code == 200
        assert graded.data['status'] == 'graded'
        assert graded.data['score'] == 4.0

    def test_unknown_anti_cheat_event_is_400(self, setup):
        attempt_id = start(setup)['attempt_id']
        url = f'/api/v1/tests/attempts/{attempt_id}/events/'
        assert setup['client'].post(url, {'event_type': 'tab_blur'}).status_code == 200
        assert setup['client'].post(url, {'event_type': 'hack'}).status_code == 400

    def test_other_student_cannot_touch_attempt(self, setup, make_user, auth_client, org):
        attempt_id = start(setup)['attempt_id']
        intruder = auth_client(make_user('x@a.kz', 'student', org), org.id)
        assert intruder.post(f'/api/v1/tests/attempts/{attempt_id}/submit/').status_code == 404
        assert intruder.get(f'/api/v1/tests/attempts/{attempt_id}/').status_code == 404

    def test_missing_test_is_404(self, setup):
        assert setup['client'].post('/api/v1/tests/999999/attempts/').status_code == 404
