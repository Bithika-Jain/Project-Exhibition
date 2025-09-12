from django.db import models
from django.contrib.auth.models import User

# Faculty model (extends default User)
class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# Student model (extends default User)
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20, unique=True)
    course = models.CharField(max_length=100)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# Project proposed by a faculty. It is reviewed by a committee (other faculties).
class Project(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='proposals')
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    timeline = models.CharField(max_length=255, blank=True)
    difficulty = models.CharField(
        max_length=20,
        choices=[('easy','Easy'), ('medium','Medium'), ('hard','Hard')],
        default='medium'
    )
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending"
    )
    seats = models.PositiveIntegerField(default=1)                 # number of students that can be selected
    seats_available = models.PositiveIntegerField(default=1)       # dynamic as students are selected
    is_approved = models.BooleanField(default=False)               # True only after committee approves
    is_discarded = models.BooleanField(default=False)              # True if rejected by committee
    committee = models.ManyToManyField(Faculty, related_name='committee_projects', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# Individual committee member's review/decision for a project
class ProjectReview(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='reviews')
    decision = models.CharField(max_length=12, choices=[('approve','Approve'), ('disapprove','Disapprove')])
    comment = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'reviewer')

    def __str__(self):
        return f"{self.project.title} — {self.reviewer.user.username} — {self.decision}"


# Student application to a project
class Application(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applications')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='applications')
    priority = models.PositiveSmallIntegerField(default=1)   # 1 highest, 2, 3
    cgpa = models.FloatField(null=True, blank=True)          # snapshot provided by student while applying
    skills = models.TextField(blank=True)                    # description of prerequisite skills / notes
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending','Pending'),
            ('shortlisted','Shortlisted'),
            ('selected','Selected'),
            ('rejected','Rejected')
        ],
        default='pending'
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'project')

    def __str__(self):
        return f"{self.student.user.username} -> {self.project.title} ({self.status})"

class Committee(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="committee_profile"
    )

    # 🔒 Required fields
    degree = models.CharField(max_length=255)  # e.g. PhD, MTech
    specialization = models.CharField(max_length=255)  # Area of expertise
    years_of_experience = models.PositiveIntegerField()  # Teaching/research/industry

    # 📌 Optional but useful fields
    publications_count = models.PositiveIntegerField(default=0)  # Research publications
    projects_supervised = models.PositiveIntegerField(default=0)  # Number of student projects guided
    is_active_faculty = models.BooleanField(default=True)  # Must still be employed
    approved_by_admin = models.BooleanField(default=False)  # Admin validates membership

    # Extra profile details
    bio = models.TextField(blank=True, null=True)  # Short professional summary
    linkedin = models.URLField(blank=True, null=True)  # Optional credibility

    def __str__(self):
        return f"{self.user.username} ({self.degree})"
