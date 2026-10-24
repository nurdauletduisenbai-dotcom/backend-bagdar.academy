"""
Демо-скрипт заполнения начальными данными (Seed data).
Создает:
- Организацию (Школа-лицей №1)
- Администратора, Учителя, 2 Учеников, Родителя
- 3 Курса: школьный предмет, подготовка к экзамену, кружок робототехники
- Разделы, уроки и видео-заглушки
- Банк из 30 вопросов разных типов (single, multi, number, short, match, open)
- 1 Итоговый тест с настройками таймера и автопроверки
"""
import os
import sys

import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import ParentStudentRelation, User
from apps.assessments.models import Test, TestQuestion
from apps.content.models import Lesson, Section
from apps.courses.models import Course, CourseStaff, Enrollment, Group
from apps.organizations.models import Organization, OrgMembership
from apps.questions.models import Question, QuestionOption, Topic
from apps.videos.models import Video


def run_seed():
    print("🌱 Начинаем генерацию демонстрационных данных...")

    # 1. Организация
    org, _ = Organization.objects.get_or_create(
        slug='fizmat-school',
        defaults={
            'name': 'ФизМат Лицей & Образовательный Центр',
            'timezone': 'Asia/Almaty',
            'is_active': True,
        }
    )
    print(f"✓ Организация: {org.name}")

    # 2. Пользователи
    admin_user, _ = User.objects.get_or_create(
        email='admin@fizmat.kz',
        defaults={
            'first_name': 'Данияр',
            'last_name': 'Администраторов',
            'is_staff': True,
            'is_superuser': True,
            'is_verified': True,
        }
    )
    admin_user.set_password('AdminPassword123!')
    admin_user.save()
    OrgMembership.objects.get_or_create(org=org, user=admin_user, role='admin')

    teacher_user, _ = User.objects.get_or_create(
        email='teacher@fizmat.kz',
        defaults={
            'first_name': 'Айгуль',
            'last_name': 'Преподавателева',
            'is_staff': True,
            'is_verified': True,
        }
    )
    teacher_user.set_password('TeacherPassword123!')
    teacher_user.save()
    OrgMembership.objects.get_or_create(org=org, user=teacher_user, role='teacher')

    student1, _ = User.objects.get_or_create(
        email='student1@fizmat.kz',
        defaults={
            'first_name': 'Арман',
            'last_name': 'Учеников',
            'is_verified': True,
        }
    )
    student1.set_password('StudentPassword123!')
    student1.save()
    OrgMembership.objects.get_or_create(org=org, user=student1, role='student')

    student2, _ = User.objects.get_or_create(
        email='student2@fizmat.kz',
        defaults={
            'first_name': 'Алия',
            'last_name': 'Отличникова',
            'is_verified': True,
        }
    )
    student2.set_password('StudentPassword123!')
    student2.save()
    OrgMembership.objects.get_or_create(org=org, user=student2, role='student')

    parent_user, _ = User.objects.get_or_create(
        email='parent@fizmat.kz',
        defaults={
            'first_name': 'Кайрат',
            'last_name': 'Родитель',
            'is_verified': True,
        }
    )
    parent_user.set_password('ParentPassword123!')
    parent_user.save()
    OrgMembership.objects.get_or_create(org=org, user=parent_user, role='parent')

    ParentStudentRelation.objects.get_or_create(parent=parent_user, student=student1, defaults={'is_confirmed': True})
    print("✓ Пользователи и роли успешно созданы.")

    # 3. Курсы
    c1, _ = Course.objects.get_or_create(
        org=org,
        slug='math-grade-10',
        defaults={
            'title': 'Алгебра и начала анализа (10 класс)',
            'description': 'Углубленный школьный курс математики.',
            'type': Course.CourseType.SCHOOL_SUBJECT,
            'subject': 'Математика',
            'grade_level': 10,
            'status': Course.Status.PUBLISHED,
            'price': 0.00,
            'is_free_preview_enabled': True,
            'created_by': teacher_user,
        }
    )

    c2, _ = Course.objects.get_or_create(
        org=org,
        slug='ent-prep-physics',
        defaults={
            'title': 'Интенсивная подготовка к ЕНТ/ЕГЭ по Физике',
            'description': 'Разбор всех тестовых заданий и формул.',
            'type': Course.CourseType.EXAM_PREP,
            'subject': 'Физика',
            'grade_level': 11,
            'status': Course.Status.PUBLISHED,
            'price': 25000.00,
            'is_free_preview_enabled': True,
            'created_by': teacher_user,
        }
    )

    c3, _ = Course.objects.get_or_create(
        org=org,
        slug='robotics-club',
        defaults={
            'title': 'Кружок прикладной робототехники и Arduino',
            'description': 'Программирование микроконтроллеров и мехатроника.',
            'type': Course.CourseType.CLUB,
            'subject': 'Информатика',
            'grade_level': 8,
            'status': Course.Status.PUBLISHED,
            'price': 18000.00,
            'is_free_preview_enabled': False,
            'created_by': teacher_user,
        }
    )
    # Учитель — преподаватель всех демо-курсов (иначе не сможет ими управлять)
    for course in (c1, c2, c3):
        CourseStaff.objects.get_or_create(course=course, teacher=teacher_user)
    print("✓ 3 Курса созданы: Школьный предмет, Подготовка к экзаменам, Кружок.")

    # 4. Группа и запись ученика 1
    group1, _ = Group.objects.get_or_create(course=c1, name='10 "А" класс')
    Enrollment.objects.get_or_create(
        course=c1,
        student=student1,
        defaults={
            'group': group1,
            'status': Enrollment.Status.ACTIVE,
            'access_until': timezone.now() + timedelta(days=180)
        }
    )

    # 5. Разделы, Уроки, Видео
    sec1, _ = Section.objects.get_or_create(course=c1, title='Раздел 1: Тригонометрические функции', order=1)
    lesson1, _ = Lesson.objects.get_or_create(
        section=sec1,
        title='Урок 1: Радианная мера угла и единичная окружность',
        order=1,
        defaults={'is_free_preview': True}
    )
    lesson2, _ = Lesson.objects.get_or_create(
        section=sec1,
        title='Урок 2: Формулы приведения и основные тождества',
        order=2,
        defaults={'is_free_preview': False}
    )

    Video.objects.get_or_create(
        lesson=lesson1,
        defaults={
            'youtube_video_id': 'dQw4w9WgXcQ',
            'title': 'Видеоразбор единичной тригонометрической окружности',
            'duration_seconds': 720,
            'order': 1
        }
    )
    Video.objects.get_or_create(
        lesson=lesson2,
        defaults={
            'youtube_video_id': 'kJQP7kiw5Fk',
            'title': 'Вывод формул приведения',
            'duration_seconds': 900,
            'order': 1
        }
    )
    print("✓ Уроки и защищенные видео добавлены.")

    # 6. Банк из 30 вопросов
    topic, _ = Topic.objects.get_or_create(org=org, subject='Математика', name='Тригонометрия')

    questions_data = [
        # 1-10: Single choice
        ("Чему равен $\\sin(90^\\circ)$?", "single", [("1", True), ("0", False), ("-1", False), ("1/2", False)], 1),
        ("Чему равен $\\cos(0^\\circ)$?", "single", [("1", True), ("0", False), ("-1", False), ("$\\sqrt{3}/2$", False)], 1),
        ("В какой четверти $\\sin(\\alpha) > 0$ и $\\cos(\\alpha) < 0$?", "single", [("Во второй", True), ("В первой", False), ("В третьей", False), ("В четвертой", False)], 2),
        ("Значение $\\tan(45^\\circ)$ равно:", "single", [("1", True), ("0", False), ("$\\sqrt{3}$", False), ("$\\sqrt{3}/3$", False)], 1),
        ("Чему равен $\\cos(180^\\circ)$?", "single", [("-1", True), ("1", False), ("0", False), ("1/2", False)], 1),
        ("Чему равен период функции $y = \\sin(x)$?", "single", [("$2\\pi$", True), ("$\\pi$", False), ("$\\pi/2$", False), ("$4\\pi$", False)], 2),
        ("Чему равен период функции $y = \\tan(x)$?", "single", [("$\\pi$", True), ("$2\\pi$", False), ("$\\pi/2$", False), ("$3\\pi$", False)], 2),
        ("Формула основного тригонометрического тождества:", "single", [("$\\sin^2 x + \\cos^2 x = 1$", True), ("$\\sin^2 x - \\cos^2 x = 1$", False), ("$\\tan x \\cdot \\cot x = 0$", False)], 1),
        ("Значение $\\sin(30^\\circ)$ равно:", "single", [("0.5", True), ("1", False), ("$\\sqrt{3}/2$", False), ("$\\sqrt{2}/2$", False)], 1),
        ("Значение $\\cos(60^\\circ)$ равно:", "single", [("0.5", True), ("0", False), ("1", False), ("-0.5", False)], 1),

        # 11-16: Multi choice
        ("Какие из функций являются нечетными?", "multi", [("$\\sin(x)$", True), ("$\\tan(x)$", True), ("$\\cos(x)$", False), ("$x^2$", False)], 3),
        ("В каких четвертях синус принимает положительные значения?", "multi", [("I четверть", True), ("II четверть", True), ("III четверть", False), ("IV четверть", False)], 2),
        ("Какие значения может принимать функция $\\cos(x)$?", "multi", [("-0.8", True), ("0.95", True), ("1.5", False), ("-2.1", False)], 2),
        ("Какие из тождеств верны?", "multi", [("$\\tan x = \\sin x / \\cos x$", True), ("$1 + \\tan^2 x = 1/\\cos^2 x$", True), ("$\\sin(2x) = 2\\sin x$", False)], 3),
        ("Выберите верные равенства для формул приведения:", "multi", [("$\\sin(\\pi - x) = \\sin x$", True), ("$\\cos(\\pi - x) = -\\cos x$", True), ("$\\sin(\\pi/2 - x) = -\\cos x$", False)], 3),
        ("В каких четвертях косинус отрицателен?", "multi", [("II четверть", True), ("III четверть", True), ("I четверть", False), ("IV четверть", False)], 2),

        # 17-22: Number with tolerance
        ("Вычислите $\\sin^2(37^\\circ) + \\cos^2(37^\\circ)$:", "number", [("1", True)], 2),
        ("Чему равен $\\cos(90^\\circ)$?", "number", [("0", True)], 1),
        ("Вычислите $2 \\cdot \\sin(30^\\circ)$:", "number", [("1", True)], 1),
        ("Вычислите $4 \\cdot \\cos(60^\\circ)$:", "number", [("2", True)], 2),
        ("Чему равен $\\tan(0)$?", "number", [("0", True)], 1),
        ("Вычислите $3 \\cdot \\tan(45^\\circ)$:", "number", [("3", True)], 1),

        # 23-26: Short text
        ("Назовите ось, на которой откладываются значения косинуса (абсцисс / ординат):", "short", [("абсцисс", True)], 2),
        ("Как называется отношение противолежащего катета к прилежащему?", "short", [("тангенс", True)], 2),
        ("Единица измерения углов, равная дуге, длина которой равна радиусу:", "short", [("радиан", True)], 2),
        ("Как называется отношение прилежащего катета к гипотенузе?", "short", [("косинус", True)], 2),

        # 27-28: Match
        ("Сопоставьте функцию и ее значение при $x = 0$:", "match", [("sin(0)", True, "0"), ("cos(0)", True, "1")], 3),
        ("Сопоставьте углы в градусах и радианах:", "match", [("180 градусов", True, "pi"), ("90 градусов", True, "pi/2")], 3),

        # 29-30: Open
        ("Докажите формулу двойного угла $\\cos(2x) = \\cos^2(x) - \\sin^2(x)$:", "open", [], 4),
        ("Опишите физический смысл гармонических колебаний через тригонометрию:", "open", [], 4),
    ]

    created_questions = []
    for text, q_type, opts, diff in questions_data:
        q, _ = Question.objects.get_or_create(
            topic=topic,
            text=text,
            type=q_type,
            defaults={
                'difficulty': diff,
                'explanation': 'Подробное математическое решение задания.',
                'created_by': teacher_user,
            }
        )
        created_questions.append(q)
        for opt_item in opts:
            if len(opt_item) == 2:
                opt_text, is_corr = opt_item
                target = ''
            else:
                opt_text, is_corr, target = opt_item
            QuestionOption.objects.get_or_create(
                question=q,
                text=opt_text,
                defaults={'is_correct': is_corr, 'match_target': target}
            )

    print(f"✓ Банк вопросов создан: ровно {len(created_questions)} вопросов всех 6 типов.")

    # 7. Итоговый тест
    test1, _ = Test.objects.get_or_create(
        course=c1,
        lesson=lesson1,
        title='Проверочный тест по тригонометрии (10 класс)',
        defaults={
            'description': 'Тест для самопроверки и контроля усвоения радианной меры и базовых формул.',
            'mode': Test.Mode.QUIZ,
            'time_limit_minutes': 20,
            'max_attempts': 3,
            'passing_score_pct': 70,
            'shuffle_questions': True,
            'shuffle_options': True,
            'show_answers_after_submit': True,
        }
    )

    # Прикрепляем первые 10 вопросов к тесту
    for idx, q in enumerate(created_questions[:10], start=1):
        TestQuestion.objects.get_or_create(test=test1, question=q, defaults={'order': idx, 'points': 1.0})

    print("✓ Тест с вопросами успешно сформирован.")

    seed_role_demo(org, admin_user, teacher_user, student1, student2, parent_user, c1, c2, c3, group1,
                   lesson1, lesson2, topic)
    seed_news()
    print("\n🎉 Все демонстрационные данные успешно загружены!")
    print_demo_accounts()


DEMO_ACCOUNTS = [
    ('Администратор', 'admin@fizmat.kz', 'AdminPassword123!'),
    ('Учитель', 'teacher@fizmat.kz', 'TeacherPassword123!'),
    ('Куратор', 'curator@fizmat.kz', 'CuratorPassword123!'),
    ('Ученик', 'student1@fizmat.kz', 'StudentPassword123!'),
    ('Ученик 2', 'student2@fizmat.kz', 'StudentPassword123!'),
    ('Родитель', 'parent@fizmat.kz', 'ParentPassword123!'),
    ('Две школы', 'multi@fizmat.kz', 'MultiPassword123!'),
    ('Админ Школы №2', 'admin@school2.kz', 'School2Password123!'),
    ('Django admin (/admin/)', 'superadmin@edu.local', 'SuperAdminPassword123!'),
]


def print_demo_accounts():
    print("\nДемо-аккаунты:")
    for role, email, password in DEMO_ACCOUNTS:
        print(f"  {role:<24} {email:<24} {password}")


def _user(email, password, first, last, **extra):
    user, _ = User.objects.get_or_create(email=email, defaults={'first_name': first, 'last_name': last,
                                                                'is_verified': True, **extra})
    user.set_password(password)
    for key, value in extra.items():
        setattr(user, key, value)
    user.save()
    return user


def seed_role_demo(org, admin_user, teacher_user, student1, student2, parent_user, c1, c2, c3, group1,
                   lesson1, lesson2, topic):
    """Данные, чтобы каждую роль можно было сразу проверить руками."""
    from apps.assignments.models import Assignment, AssignmentSubmission
    from apps.notifications.models import Announcement
    from apps.payments.models import Order
    from apps.schedule.models import Session

    now = timezone.now()

    # Админ школы — не суперпользователь, чтобы видеть ровно права роли «admin».
    admin_user.is_superuser = False
    admin_user.is_staff = False
    admin_user.save(update_fields=['is_superuser', 'is_staff'])
    _user('superadmin@edu.local', 'SuperAdminPassword123!', 'Супер', 'Админ', is_staff=True, is_superuser=True)

    curator = _user('curator@fizmat.kz', 'CuratorPassword123!', 'Мадина', 'Кураторова')
    OrgMembership.objects.get_or_create(org=org, user=curator, role='curator')

    # Вторая школа: изоляция данных + пользователь в двух организациях
    school2, _ = Organization.objects.get_or_create(slug='school-2', defaults={'name': 'Школа №2', 'timezone': 'Asia/Almaty'})
    admin2 = _user('admin@school2.kz', 'School2Password123!', 'Ерлан', 'Директоров')
    OrgMembership.objects.get_or_create(org=school2, user=admin2, role='admin')
    multi = _user('multi@fizmat.kz', 'MultiPassword123!', 'Тимур', 'Двухшкольный')
    OrgMembership.objects.get_or_create(org=org, user=multi, role='student')
    OrgMembership.objects.get_or_create(org=school2, user=multi, role='teacher')
    s2course, _ = Course.objects.get_or_create(org=school2, slug='chemistry-9', defaults={
        'title': 'Химия 9 класс (Школа №2)', 'type': Course.CourseType.SCHOOL_SUBJECT, 'subject': 'Химия',
        'grade_level': 9, 'status': Course.Status.PUBLISHED, 'created_by': admin2,
    })
    CourseStaff.objects.get_or_create(course=s2course, teacher=multi)
    s2section, _ = Section.objects.get_or_create(course=s2course, title='Раздел 1: Строение атома', order=1)
    Lesson.objects.get_or_create(section=s2section, title='Периодическая таблица', defaults={'order': 1})
    Enrollment.objects.get_or_create(course=c1, student=multi, defaults={
        'group': group1, 'status': Enrollment.Status.ACTIVE, 'access_until': now + timedelta(days=180)})

    # Ученик 2 записан на кружок; ЕНТ-физику можно купить; висит заказ на подтверждение админом
    Enrollment.objects.get_or_create(course=c3, student=student2, defaults={
        'status': Enrollment.Status.ACTIVE, 'access_until': now + timedelta(days=90)})
    Order.objects.get_or_create(idempotency_key='demo-pending-order', defaults={
        'user': student2, 'course': c2, 'amount': c2.price, 'provider': Order.Provider.MANUAL})

    # Расписание группы 10 «А» на ближайшие дни
    for day, (title, hour, url) in enumerate([
        ('Тригонометрический круг', 15, 'https://meet.google.com/demo-edu-1'),
        ('Формулы приведения', 16, ''),
        ('Контрольная работа', 15, ''),
    ], start=1):
        start = (now + timedelta(days=day)).replace(hour=hour, minute=0, second=0, microsecond=0)
        Session.objects.get_or_create(group=group1, title=title, defaults={
            'start_time': start, 'end_time': start + timedelta(minutes=90),
            'location': 'Каб. 204', 'online_meeting_url': url or None, 'lesson': lesson1})

    # Задания: одно сдано и ждёт проверки, одно открыто
    hw1, _ = Assignment.objects.get_or_create(lesson=lesson1, title='Задачи на единичную окружность', defaults={
        'description': 'Решите задачи 1–10 из конспекта и приложите фото решения.',
        'deadline': now + timedelta(days=3), 'max_score': 10, 'created_by': teacher_user})
    Assignment.objects.get_or_create(lesson=lesson2, title='Доказательство формул', defaults={
        'description': 'Докажите формулы приведения для sin и cos.',
        'deadline': now + timedelta(days=7), 'max_score': 20, 'created_by': teacher_user})
    AssignmentSubmission.objects.get_or_create(assignment=hw1, student=student1, defaults={
        'text_content': 'Решения задач 1–10:\n1) sin 30° = 1/2\n2) cos 60° = 1/2\n...'})

    # Открытый вопрос в отдельном тесте — учителю есть что проверить вручную
    open_q, _ = Question.objects.get_or_create(topic=topic, text='Объясните своими словами, что такое радиан.',
                                               defaults={'type': 'open', 'difficulty': 2, 'created_by': teacher_user})
    essay, _ = Test.objects.get_or_create(course=c1, title='Мини-эссе: радианная мера', defaults={
        'mode': Test.Mode.PRACTICE, 'time_limit_minutes': 0, 'max_attempts': 3, 'passing_score_pct': 50})
    TestQuestion.objects.get_or_create(test=essay, question=open_q, defaults={'order': 1, 'points': 5})

    Announcement.objects.get_or_create(org=org, title='Добро пожаловать в EduPlatform!', defaults={
        'content': 'Это демо-объявление для всей школы. Расписание — в разделе «Расписание».',
        'created_by': admin_user})
    Announcement.objects.get_or_create(org=org, course=c1, title='Контрольная по тригонометрии', defaults={
        'content': 'Через 3 дня — контрольная. Повторите формулы приведения.', 'created_by': teacher_user})
    print("✓ Демо-данные для ролей: куратор, вторая школа, расписание, задания, заказ, объявления.")


def seed_news():
    """Публикации для публичной главной страницы (новости платформы, не привязаны к школе)."""
    from apps.news.models import Post

    now = timezone.now()
    posts = [
        dict(title='bagdar.academy: учитесь думать, а не просто сдавать', category=Post.Category.UPDATE,
             is_pinned=True, days_ago=1,
             excerpt='Видеоуроки, тесты, домашние задания и расписание — в одном месте для учеников, '
                     'родителей и учителей.',
             body='bagdar.academy — образовательная платформа для школ и учебных центров Казахстана.\n\n'
                  'Ученик смотрит видеоуроки, решает тесты с разбором ошибок и сдаёт домашние задания онлайн. '
                  'Учитель собирает курс из уроков, видео и вопросов банка, проверяет работы и видит прогресс '
                  'каждого ученика. Родитель в любой момент открывает отчёт об успеваемости ребёнка.\n\n'
                  'Чтобы начать, зарегистрируйтесь или получите приглашение от своей школы.'),
        dict(title='ҰБТ-ға дайындық курстары ашылды', category=Post.Category.NEWS, days_ago=3,
             excerpt='Математика, физика және оқу сауаттылығы бойынша жаңа курстар: бейнесабақтар, '
                     'сынақ тесттері және мұғалімнің кері байланысы.',
             body='Жаңа оқу жылында платформада ҰБТ-ға дайындыққа арналған курстар қолжетімді болды.\n\n'
                  'Әр курс тақырыптық бөлімдерден, бейнесабақтардан және нақты емтихан форматындағы '
                  'сынақ тесттерінен тұрады. Тесттен кейін әр сұрақтың толық талдауы көрсетіледі.\n\n'
                  'Курсқа жазылу үшін тіркеліп, каталогтан қажетті пәнді таңдаңыз.'),
        dict(title='Как родителю следить за успеваемостью ребёнка', category=Post.Category.ARTICLE, days_ago=6,
             excerpt='Привяжите аккаунт ребёнка — и отчёт по урокам, тестам, заданиям и посещаемости '
                     'всегда будет под рукой.',
             body='Зарегистрируйтесь с ролью «Родитель» и в разделе «Мои дети» укажите email ребёнка. '
                  'Ребёнок подтвердит запрос в своём кабинете.\n\n'
                  'После этого вы увидите пройденные уроки, результаты тестов, оценки за задания и отметки '
                  'посещаемости по каждому курсу. Уведомления о новых оценках приходят автоматически.'),
        dict(title='Открытый онлайн-урок: тригонометрия за 90 минут', category=Post.Category.EVENT, days_ago=8,
             excerpt='Разберём единичную окружность и формулы приведения. Урок бесплатный — '
                     'нужна только регистрация.',
             body='Приглашаем учеников 9–11 классов на открытый онлайн-урок.\n\n'
                  'Программа: радианная мера, единичная окружность, формулы приведения и типичные ошибки на '
                  'экзамене. После урока — короткий тест с мгновенной проверкой.\n\n'
                  'Ссылка на трансляцию появится в расписании после регистрации.'),
        dict(title='Мұғалімдерге: курс конструкторы және сұрақтар банкі', category=Post.Category.ARTICLE,
             days_ago=12,
             excerpt='Курсты бөлімдер мен сабақтардан құрастырыңыз, сұрақтарды банкте сақтап, '
                     'тесттерде қайта пайдаланыңыз.',
             body='Курс конструкторында бөлімдер мен сабақтарды қосып, бейне мен материалдарды тіркеуге болады.\n\n'
                  'Сұрақтар банкі алты түрлі сұрақты қолдайды: бір жауап, бірнеше жауап, қысқа мәтін, сан, '
                  'сәйкестендіру және кеңейтілген жауап. Бір сұрақты бірнеше тестте қолдануға болады.'),
    ]
    for item in posts:
        days_ago = item.pop('days_ago')
        Post.objects.get_or_create(title=item['title'], defaults={
            **item, 'is_published': True, 'published_at': now - timedelta(days=days_ago)})
    print(f"✓ Новости для главной страницы: {len(posts)} публикаций.")


if __name__ == '__main__':
    run_seed()
