from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ExcelUploadView,
    HighestScorerView,
    StudentTestViewSet,
    TestViewSet,
    WeeklyCombinedAnalyticsView,
)

router = DefaultRouter()

router.register(r"student-test", StudentTestViewSet, basename="student-test")
router.register(r"available-test", TestViewSet, basename="test")

urlpatterns = [
    path("", include(router.urls)),
    path("upload-excel/", ExcelUploadView.as_view(), name="upload-excel"),
    path("highest-scorer/", HighestScorerView.as_view(), name="highest-scorer"),
    path("analytics/", WeeklyCombinedAnalyticsView.as_view(), name="analytics"),
]
