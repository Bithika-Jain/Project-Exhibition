from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Faculty, Student, Project, Application, Committee
from .serializers import FacultySerializer, StudentSerializer, ProjectSerializer, ApplicationSerializer, CommitteeSerializer
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import make_password

# Faculty API
class FacultyViewSet(viewsets.ModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer


# Student API
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


# Custom permission: only project owner (student) can edit/delete
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.student.user == request.user

#Project API
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(faculty=self.request.user.faculty_profile)

    # ✅ Custom action for Approve
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        project = self.get_object()
        # Only committee members can approve
        if not hasattr(request.user, "committee_profile") or not request.user.committee_profile.approved_by_admin:
            return Response({"error": "Only approved committee members can approve projects."},
                            status=status.HTTP_403_FORBIDDEN)

        project.status = "approved"
        project.is_approved = True
        project.is_discarded = False
        project.save()
        return Response({"message": f"Project '{project.title}' approved successfully!",
                         "status": project.status})

    # ✅ Custom action for Reject
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        project = self.get_object()
        # Only committee members can reject
        if not hasattr(request.user, "committee_profile") or not request.user.committee_profile.approved_by_admin:
            return Response({"error": "Only approved committee members can reject projects."},
                            status=status.HTTP_403_FORBIDDEN)

        project.status = "rejected"
        project.is_approved = False
        project.is_discarded = True
        project.save()
        return Response({"message": f"Project '{project.title}' rejected successfully!",
                         "status": project.status})



# Application API
class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        When a student creates an application, set the student automatically from request.user.
        Frontend should POST { "project": <project_id> } only.
        Prevent duplicate applications by the same student to the same project.
        """
        try:
            student = Student.objects.get(user=self.request.user)
        except Student.DoesNotExist:
            raise ValidationError("Only students can apply to projects.")

        project = serializer.validated_data.get('project')
        if Application.objects.filter(student=student, project=project).exists():
            raise ValidationError("You have already applied to this project.")

        serializer.save(student=student)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my(self, request):
        """
        Return applications submitted by the logged-in student.
        GET /api/applications/my/
        """
        apps = Application.objects.filter(student__user=request.user)
        serializer = self.get_serializer(apps, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def faculty_applications(self, request):
        """
        Return all applications for projects created by the logged-in faculty.
        GET /api/applications/faculty_applications/
        """
        apps = Application.objects.filter(project__faculty__user=request.user)
        serializer = self.get_serializer(apps, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request, pk=None):
        """
        Faculty accepts an application -> sets status = 'accepted'
        POST /api/applications/{id}/accept/
        """
        app = self.get_object()
        if app.project.faculty.user != request.user:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)
        app.status = "accepted"
        app.save()
        return Response(self.get_serializer(app).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        """
        Faculty rejects an application -> sets status = 'rejected'
        POST /api/applications/{id}/reject/
        """
        app = self.get_object()
        if app.project.faculty.user != request.user:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)
        app.status = "rejected"
        app.save()
        return Response(self.get_serializer(app).data)

@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    data = request.data
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if not username or not password or not role:
        return Response({"error": "username, password and role are required"},
                        status=status.HTTP_400_BAD_REQUEST)

    # ✅ check if username already exists
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already taken"},
                        status=status.HTTP_400_BAD_REQUEST)

    # ✅ create user with hashed password
    user = User.objects.create(
        username=username,
        password=make_password(password)
    )

    # ✅ attach role-specific profile
    if role == "student":
        Student.objects.create(
            user=user,
            roll_number=data.get("roll_number", "TEMP123"),
            course=data.get("course", "Unknown")
        )
    elif role == "faculty":
        Faculty.objects.create(
            user=user,
            department=data.get("department", "General")
        )
    else:
        return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Signup successful"}, status=status.HTTP_201_CREATED)

class CommitteeViewSet(viewsets.ModelViewSet):
    queryset = Committee.objects.all()
    serializer_class = CommitteeSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def apply(self, request):
        """Custom endpoint for faculty to apply as committee member"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, approved_by_admin=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)