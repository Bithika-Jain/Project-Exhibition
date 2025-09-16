🎓 Project Exhibition Portal

A web application to manage faculty projects, student applications, and committee reviews for college project exhibitions.

🚀 Features (Planned & Implemented)
✅ Already Implemented

Authentication (JWT)

  Signup (student/faculty)

  Login → receive access/refresh tokens

Faculty

  Create projects (auto-pending approval)

  View their own projects (/api/projects/my/)

Committee

  Apply to become committee member

  Admin approves/rejects committee applications

General

  Project listing API



⏳ To Be Implemented

Student

 Apply to project

 Prevent duplicate applications

 Limit applications per student (e.g., 3 max)

Committee

 Approve/reject projects (optional, if time allows)


Frontend Integration

 Connect signup/login with backend

 Show projects (faculty vs student views)

 Apply to project button

 Committee approval dashboard


🛠 Tech Stack

Backend: Django + Django REST Framework + SimpleJWT

Frontend: HTML, CSS, JavaScript (provided in repo)

Database: SQLite (default)


📂 Project Setup
1. Clone the repo
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

2. Setup virtual environment
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

3. Install dependencies
pip install -r requirements.txt

4. Run migrations
python manage.py makemigrations
python manage.py migrate

5. Run server
python manage.py runserver


🔑 API Endpoints (Main)

Auth

 POST /api/signup/ → create student/faculty

 POST /api/auth/login/ → login (JWT access/refresh)

Faculty

 POST /api/projects/ → create new project

 GET /api/projects/my/ → list own projects

Student

 POST /api/applications/ → apply to a project (to be added)

Committee

 POST /api/committees/apply/ → apply for committee membership

 PATCH /api/committees/{id}/ → approve/reject



📂 Backend Project Structure
exhibition_backend/                # Django project root
│
├── exhibition_backend/            # Project settings folder
│   ├── settings.py                # Django + REST + JWT setup
│   ├── urls.py                    # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                          # Main app (models, views, etc.)
│   ├── models.py                  # Faculty, Student, Project, Application, Committee
│   ├── serializers.py             # Converts models <-> JSON
│   ├── views.py                   # API logic (ViewSets, signup, committee apply, etc.)
│   ├── urls.py                    # API routes (faculty, students, projects, applications, committees)
│   ├── admin.py                   # Register models in Django admin
│   ├── apps.py
│   └── migrations/                # Database schema versions
│
├── manage.py                      # Django CLI entry point
└── db.sqlite3                     # SQLite database (auto-created)



🔑 Where to Add/Edit Things

 Models (core/models.py) → define database tables (Faculty, Student, Project, Application, Committee).

 Serializers (core/serializers.py) → convert models to JSON & validate input.

 Views (core/views.py) → main backend logic (CRUD APIs, custom actions like /apply/).

 URLs (core/urls.py) → define API endpoints (faculty, students, projects, applications, committees).

 Settings (exhibition_backend/settings.py) → enable JWT auth, CORS, REST framework.



⚡ Quick Pointers 

When adding a new rule (like student application limit):
→ Write logic inside core/views.py (probably in ApplicationViewSet).

When changing what data comes in/out of APIs:
→ Update core/serializers.py.

When changing the database schema (new field, relation):
→ Edit core/models.py, run:

python manage.py makemigrations
python manage.py migrate


New APIs (like /committees/apply/):
→ Add a method in views.py and wire it in urls.py.