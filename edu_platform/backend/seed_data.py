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
    print("\n🎉 Все демонстрационные данные успешно загружены!")


if __name__ == '__main__':
    run_seed()
