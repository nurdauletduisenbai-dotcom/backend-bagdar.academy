from django.db.models import Avg, Count, Max, Q
from django.utils import timezone

from apps.content.models import Lesson
from apps.courses.models import Course, Enrollment

from .models import CourseProgress, LessonProgress

FINISHED_ATTEMPT_STATUSES = ('submitted', 'graded', 'expired')


def published_lessons(course: Course):
    now = timezone.now()
    return Lesson.objects.filter(section__course=course).filter(Q(publish_at__isnull=True) | Q(publish_at__lte=now))


class ProgressService:
    @classmethod
    def mark_lesson_completed(cls, student, lesson: Lesson) -> LessonProgress:
        progress, _ = LessonProgress.objects.get_or_create(lesson=lesson, student=student)
        cls.recalculate(student, lesson.section.course)
        return progress

    @classmethod
    def on_video_completed(cls, student, video):
        """Все видео урока просмотрены → урок пройден."""
        from apps.videos.models import Video, VideoProgress
        lesson = video.lesson
        total = Video.objects.filter(lesson=lesson).count()
        done = VideoProgress.objects.filter(video__lesson=lesson, student=student, is_completed=True).count()
        if total and done >= total:
            cls.mark_lesson_completed(student, lesson)

    @classmethod
    def best_test_scores(cls, student, course: Course) -> dict[int, float]:
        from apps.assessments.models import TestAttempt
        rows = (
            TestAttempt.objects.filter(student=student, test__course=course, status__in=FINISHED_ATTEMPT_STATUSES)
            .values('test_id')
            .annotate(best=Max('score_pct'))
        )
        return {r['test_id']: r['best'] for r in rows}

    @classmethod
    def recalculate(cls, student, course: Course) -> CourseProgress | None:
        enrollment = Enrollment.objects.filter(student=student, course=course).first()
        if not enrollment:
            return None
        lesson_ids = list(published_lessons(course).values_list('id', flat=True))
        completed = LessonProgress.objects.filter(student=student, lesson_id__in=lesson_ids).count()
        best = cls.best_test_scores(student, course)

        progress, _ = CourseProgress.objects.get_or_create(enrollment=enrollment)
        progress.total_lessons_count = len(lesson_ids)
        progress.lessons_completed_count = completed
        progress.percent_completed = round(completed / len(lesson_ids) * 100, 1) if lesson_ids else 0.0
        progress.average_test_score = round(sum(best.values()) / len(best), 1) if best else 0.0
        progress.save()
        return progress

    @classmethod
    def course_report(cls, student, course: Course) -> dict:
        """Полный отчёт ученика по курсу: уроки, тесты, задания, посещаемость."""
        from apps.assessments.models import Test, TestAttempt
        from apps.assignments.models import Assignment, AssignmentSubmission
        from apps.schedule.models import Attendance

        progress = cls.recalculate(student, course)
        completed_ids = set(
            LessonProgress.objects.filter(student=student, lesson__section__course=course).values_list('lesson_id', flat=True)
        )
        lessons = [
            {'id': lesson.id, 'title': lesson.title, 'section': lesson.section.title, 'is_completed': lesson.id in completed_ids}
            for lesson in published_lessons(course).select_related('section').order_by('section__order', 'order', 'id')
        ]

        best = cls.best_test_scores(student, course)
        attempts_count = dict(
            TestAttempt.objects.filter(student=student, test__course=course)
            .values('test_id').annotate(n=Count('id')).values_list('test_id', 'n')
        )
        tests = [
            {'id': t.id, 'title': t.title, 'best_score_pct': best.get(t.id), 'attempts': attempts_count.get(t.id, 0),
             'passed': best.get(t.id) is not None and best[t.id] >= t.passing_score_pct}
            for t in Test.objects.filter(course=course).order_by('id')
        ]

        submissions = {
            s.assignment_id: s
            for s in AssignmentSubmission.objects.filter(student=student, assignment__lesson__section__course=course)
        }
        assignments = []
        for a in Assignment.objects.filter(lesson__section__course=course).order_by('deadline'):
            sub = submissions.get(a.id)
            assignments.append({
                'id': a.id, 'title': a.title, 'deadline': a.deadline, 'max_score': a.max_score,
                'status': 'graded' if sub and sub.graded_at else ('submitted' if sub else
                          ('overdue' if a.deadline < timezone.now() else 'pending')),
                'score': sub.score if sub else None,
            })

        attendance = dict(
            Attendance.objects.filter(student=student, session__group__course=course)
            .values('status').annotate(n=Count('id')).values_list('status', 'n')
        )

        return {
            'course_id': course.id,
            'course_title': course.title,
            'percent_completed': progress.percent_completed if progress else 0.0,
            'lessons_completed_count': progress.lessons_completed_count if progress else 0,
            'total_lessons_count': progress.total_lessons_count if progress else len(lessons),
            'average_test_score': progress.average_test_score if progress else 0.0,
            'lessons': lessons,
            'tests': tests,
            'assignments': assignments,
            'attendance': attendance,
        }

    @classmethod
    def course_students_table(cls, course: Course) -> list[dict]:
        """Таблица прогресса всех учеников курса (для учителя)."""
        from apps.assessments.models import TestAttempt
        enrollments = Enrollment.objects.filter(course=course).select_related('student', 'group')
        avg_scores = dict(
            TestAttempt.objects.filter(test__course=course, status__in=FINISHED_ATTEMPT_STATUSES)
            .values('student_id').annotate(avg=Avg('score_pct')).values_list('student_id', 'avg')
        )
        rows = []
        for e in enrollments:
            progress = cls.recalculate(e.student, course)
            rows.append({
                'student_id': e.student_id,
                'student_email': e.student.email,
                'student_name': e.student.get_full_name(),
                'group': e.group.name if e.group else None,
                'enrollment_status': e.status,
                'percent_completed': progress.percent_completed if progress else 0.0,
                'average_test_score': round(avg_scores.get(e.student_id) or 0.0, 1),
            })
        return rows
