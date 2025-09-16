from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FacultyViewSet, StudentViewSet, ProjectViewSet, ApplicationViewSet, signup, CommitteeViewSet

# Router will automatically generate API routes for us
router = DefaultRouter()
router.register(r'faculty', FacultyViewSet)
router.register(r'students', StudentViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'committees', CommitteeViewSet, basename='committee')


urlpatterns = [
    path('', include(router.urls)),
    path('signup/', signup, name='signup'),  # ✅ add this line
]
