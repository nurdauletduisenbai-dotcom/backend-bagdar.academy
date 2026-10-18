from django.urls import path

from .views import CourseProgressView, CourseStudentsProgressView, MyProgressView, OrgSummaryView, StudentProgressView

urlpatterns = [
    path('my/', MyProgressView.as_view(), name='progress_my'),
    path('courses/<int:course_id>/', CourseProgressView.as_view(), name='progress_course'),
    path('courses/<int:course_id>/students/', CourseStudentsProgressView.as_view(), name='progress_course_students'),
    path('students/<int:student_id>/', StudentProgressView.as_view(), name='progress_student'),
    path('org/summary/', OrgSummaryView.as_view(), name='progress_org_summary'),
]
