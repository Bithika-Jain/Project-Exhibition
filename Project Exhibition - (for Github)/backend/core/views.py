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
from django.db.models import Count

# Custom permission: only allow access based on user role
class IsFacultyUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            Faculty.objects.get(user=request.user)
            return True
        except Faculty.DoesNotExist:
            return False

class IsStudentUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            Student.objects.get(user=request.user)
            return True
        except Student.DoesNotExist:
            return False

# Faculty API
class FacultyViewSet(viewsets.ModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    permission_classes = [IsFacultyUser]

# Student API
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsStudentUser]

# Custom permission: only project owner (faculty) can edit/delete
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'faculty'):
            return obj.faculty.user == request.user
        return obj.student.user == request.user

# Project API
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Project.objects.annotate(applications_count=Count('applications'))
        # Students can only see approved projects
        if hasattr(self.request.user, 'student'):
            return queryset.filter(is_approved=True)
        return queryset

    def perform_create(self, serializer):
        try:
            faculty = Faculty.objects.get(user=self.request.user)
        except Faculty.DoesNotExist:
            raise ValidationError("Only faculty members can create projects.")
        
        seats = serializer.validated_data.get('seats', 1)
        # All new projects start as pending and not approved
        serializer.save(
            faculty=faculty, 
            seats_available=seats,
            status='pending',
            is_approved=False
        )

    @action(detail=False, methods=['get'], permission_classes=[IsFacultyUser])
    def my(self, request):
        """Return projects created by the currently logged-in faculty."""
        try:
            faculty = Faculty.objects.get(user=request.user)
            faculty_projects = Project.objects.filter(faculty=faculty).annotate(
                applications_count=Count('applications')
            )
            serializer = self.get_serializer(faculty_projects, many=True)
            return Response(serializer.data)
        except Faculty.DoesNotExist:
            return Response({"error": "Faculty profile not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[IsFacultyUser])
    def pending_review(self, request):
        """Return projects pending review for committee members."""
        try:
            # Check if user is a committee member
            if not hasattr(request.user, 'committee_profile'):
                return Response({"error": "Only committee members can review projects."}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            committee_profile = request.user.committee_profile
            if not committee_profile.approved_by_admin:
                return Response({"error": "Only approved committee members can review projects."}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            # Get faculty profile to determine department
            try:
                faculty = Faculty.objects.get(user=request.user)
            except Faculty.DoesNotExist:
                return Response({"error": "Committee member must also have faculty profile"}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Get projects from same department that are pending (exclude own projects)
            pending_projects = Project.objects.filter(
                faculty__department=faculty.department,
                status='pending',
                is_approved=False
            ).exclude(faculty=faculty).select_related('faculty__user')
            
            # Add faculty name to the serialized data
            projects_data = []
            for project in pending_projects:
                project_data = self.get_serializer(project).data
                project_data['faculty_name'] = f"{project.faculty.user.first_name} {project.faculty.user.last_name}".strip() or project.faculty.user.username
                projects_data.append(project_data)
            
            return Response(projects_data)
            
        except Exception as e:
            return Response({"error": f"Error fetching pending projects: {str(e)}"}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], permission_classes=[IsFacultyUser])
    def approve(self, request, pk=None):
        project = self.get_object()
        try:
            # Check if user is committee member
            if not hasattr(request.user, "committee_profile") or not request.user.committee_profile.approved_by_admin:
                return Response({"error": "Only approved committee members can approve projects."},
                                status=status.HTTP_403_FORBIDDEN)
            
            # Get faculty profile to check department
            faculty = Faculty.objects.get(user=request.user)
            
            # Check if it's same department
            if project.faculty.department != faculty.department:
                return Response({"error": "You can only review projects from your department."},
                                status=status.HTTP_403_FORBIDDEN)

            project.status = "approved"
            project.is_approved = True
            project.is_discarded = False
            project.save()
            return Response({"message": f"Project '{project.title}' approved successfully!"})
        except Faculty.DoesNotExist:
            return Response({"error": "Faculty profile not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], permission_classes=[IsFacultyUser])
    def reject(self, request, pk=None):
        project = self.get_object()
        try:
            # Check if user is committee member
            if not hasattr(request.user, "committee_profile") or not request.user.committee_profile.approved_by_admin:
                return Response({"error": "Only approved committee members can reject projects."},
                                status=status.HTTP_403_FORBIDDEN)
            
            # Get faculty profile to check department
            faculty = Faculty.objects.get(user=request.user)
            
            # Check if it's same department
            if project.faculty.department != faculty.department:
                return Response({"error": "You can only review projects from your department."},
                                status=status.HTTP_403_FORBIDDEN)

            project.status = "rejected"
            project.is_approved = False
            project.is_discarded = True
            project.save()
            return Response({"message": f"Project '{project.title}' rejected successfully!"})
        except Faculty.DoesNotExist:
            return Response({"error": "Faculty profile not found"}, status=status.HTTP_404_NOT_FOUND)

# Application API
class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Students can apply to projects."""
        try:
            student = Student.objects.get(user=self.request.user)
        except Student.DoesNotExist:
            raise ValidationError("Only students can apply to projects.")
        
        # Check application limit
        if Application.objects.filter(student=student).count() >= 3:
            raise ValidationError("You cannot apply to more than 3 projects.")
        
        project = serializer.validated_data.get('project')
        
        # Check for duplicate applications
        if Application.objects.filter(student=student, project=project).exists():
            raise ValidationError("You have already applied to this project.")

        # Check if project has available seats
        if project.seats_available <= 0:
            raise ValidationError("No seats available for this project.")

        # Check if project is approved
        if not project.is_approved:
            raise ValidationError("This project is not yet approved for applications.")

        # Create the application
        application = serializer.save(student=student)
        
        # Decrease available seats
        if project.seats_available > 0:
            project.seats_available -= 1
            project.save()

    @action(detail=False, methods=["get"], permission_classes=[IsStudentUser])
    def my(self, request):
        """Return applications submitted by the logged-in student."""
        try:
            student = Student.objects.get(user=request.user)
            apps = Application.objects.filter(student=student)
            serializer = self.get_serializer(apps, many=True)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({"error": "Student profile not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get"], permission_classes=[IsFacultyUser])
    def faculty_applications(self, request):
        """Return all applications for projects created by the logged-in faculty."""
        try:
            faculty = Faculty.objects.get(user=request.user)
            apps = Application.objects.filter(project__faculty=faculty)
            serializer = self.get_serializer(apps, many=True)
            return Response(serializer.data)
        except Faculty.DoesNotExist:
            return Response({"error": "Faculty profile not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], permission_classes=[IsFacultyUser])
    def select(self, request, pk=None):
        """Faculty selects a student for their project."""
        app = self.get_object()
        try:
            faculty = Faculty.objects.get(user=request.user)
            if app.project.faculty != faculty:
                return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)
            
            # Check if student is already selected for another project
            if Application.objects.filter(student=app.student, status='selected').exists():
                return Response({"error": "Student is already selected for another project"}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            app.status = "selected"
            app.save()
            
            # Reject all other applications for this student
            Application.objects.filter(student=app.student).exclude(id=app.id).update(status='rejected')
            
            return Response(self.get_serializer(app).data)
        except Faculty.DoesNotExist:
            return Response({"error": "Faculty profile not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], permission_classes=[IsFacultyUser])
    def reject(self, request, pk=None):
        """Faculty rejects an application."""
        app = self.get_object()
        try:
            faculty = Faculty.objects.get(user=request.user)
            if app.project.faculty != faculty:
                return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)
            
            app.status = "rejected"
            app.save()
            
            # Increase seats_available when rejecting
            project = app.project
            project.seats_available += 1
            project.save()
            
            return Response(self.get_serializer(app).data)
        except Faculty.DoesNotExist:
            return Response({"error": "Faculty profile not found"}, status=status.HTTP_404_NOT_FOUND)

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

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already taken"},
                        status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create(
        username=username,
        password=make_password(password)
    )

    if role == "student":
        Student.objects.create(
            user=user,
            roll_number=data.get("roll_number", f"TEMP_{user.id}"),
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
    permission_classes = [IsFacultyUser]

    @action(detail=False, methods=['post'], permission_classes=[IsFacultyUser])
    def apply(self, request):
        """Custom endpoint for faculty to apply as committee member"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, approved_by_admin=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)