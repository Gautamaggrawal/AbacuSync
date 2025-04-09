from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ExcelUploadView, StudentTestViewSet, TestViewSet

router = DefaultRouter()

router.register(r"student-test", StudentTestViewSet, basename="student-test")
router.register(r"available-test", TestViewSet, basename="test")

urlpatterns = [
    path("", include(router.urls)),
    path("upload-excel/", ExcelUploadView.as_view(), name="upload-excel"),
]
