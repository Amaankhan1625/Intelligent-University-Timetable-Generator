from django.urls import path, include
from rest_framework import routers
from scheduler_app import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# ---------------------
# REST Framework Router
# ---------------------
router = routers.DefaultRouter()
router.register(r'instructors', views.InstructorViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'meeting-times', views.MeetingTimeViewSet)
router.register(r'departments', views.DepartmentViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'sections', views.SectionViewSet)
router.register(r'classes', views.ClassViewSet)
router.register(r'timetables', views.TimetableViewSet)

# ---------------------
# URL Patterns
# ---------------------
urlpatterns = [
    # Core CRUD API routes
    path('', include(router.urls)),

    # JWT Authentication endpoints
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Logged-in user info endpoint for frontend
    path('auth/user/', views.get_user, name='auth_user'),

    # Optional profile endpoint
    path('auth/profile/', views.UserProfileView.as_view(), name='user_profile'),

    # Change password endpoint
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
]
