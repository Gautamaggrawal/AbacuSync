from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(
    r'centres',
    views.CentreViewSet,
    basename='centre'
)
router.register(
    r'students',
    views.StudentViewSet,
    basename='student'
)
router.register(
    r'student-level-history',
    views.StudentLevelHistoryViewSet,
    basename='student-level-history'
)
router.register(
    r'levels',
    views.LevelViewSet,
    basename='level'
)

# Authentication URLs
auth_urls = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
]

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('auth/', include(auth_urls)),
    path('', include(router.urls)),
]