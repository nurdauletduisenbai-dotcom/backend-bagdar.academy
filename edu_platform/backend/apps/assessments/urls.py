from django.urls import path

from .views import (
    AttemptDetailView,
    GradeAttemptAnswerView,
    LogAntiCheatEventView,
    SaveAttemptAnswerView,
    StartTestAttemptView,
    SubmitTestAttemptView,
    TestDetailView,
)

urlpatterns = [
    path('<int:test_id>/', TestDetailView.as_view(), name='test_detail'),
    path('<int:test_id>/attempts/', StartTestAttemptView.as_view(), name='start_test_attempt'),
    path('attempts/<int:attempt_id>/', AttemptDetailView.as_view(), name='attempt_detail'),
    path('attempts/<int:attempt_id>/answers/<int:question_id>/', SaveAttemptAnswerView.as_view(),
         name='save_test_answer'),
    path('attempts/<int:attempt_id>/answers/<int:question_id>/grade/', GradeAttemptAnswerView.as_view(),
         name='grade_test_answer'),
    path('attempts/<int:attempt_id>/events/', LogAntiCheatEventView.as_view(), name='log_anti_cheat'),
    path('attempts/<int:attempt_id>/submit/', SubmitTestAttemptView.as_view(), name='submit_test_attempt'),
]
