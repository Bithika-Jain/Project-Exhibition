from rest_framework import serializers
from .models import Faculty, Student, Project, Application, Committee

class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = [
            "faculty",       # ✅ set automatically, not from user
            "created_at",    # ✅ timestamp should be backend only
            "committee",     # ✅ decided by reviewers
            "is_discarded",  # ✅ backend only
            "seats_available"  # ✅ system-managed
        ]

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'

class CommitteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Committee
        fields = "__all__"
        read_only_fields = ["approved_by_admin", "user"]

