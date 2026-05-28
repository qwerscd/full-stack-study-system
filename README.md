# Full-Stack Study System

Thesis prototype: **Design and Development of a Full-Stack Study System**  
Author: **Chen Junshuo**

A mini web application for course registration, enrollment management, and grades, with **student** and **teacher** roles.

> **Repository:** https://github.com/qwerscd/full-stack-study-system  
> Click folders `static/`, `templates/`, `docs/` on GitHub to expand the full tree.

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python 3 + Flask |
| Database | SQLite |

## Features

- User registration and login
- Role-based access (student / teacher)
- Students: browse courses, enroll, drop courses, view my courses and grades
- Teachers: create, edit, delete courses; view students; remove enrollments; assign grades
- Business rules:
  - Maximum enrollment per course
  - No duplicate enrollment (DB unique constraint + server check)
  - Role-based permissions

## Quick start

```bash
cd /Users/chenjunshuo/Projects/study-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

### Demo accounts

| Role | Username | Password |
|------|----------|----------|
| Student | `student1` | `student123` |
| Student | `student2` | `student123` |
| Student | `student3` | `student123` |
| Teacher | `teacher1` | `teacher123` |
| Teacher | `teacher2` | `teacher123` |

**Test “course full”:** Log in as `student1` and `student2`, enroll in **CS101** (capacity 2). Then log in as `student3`, open **Browse Courses**, click **Try Enroll** on CS101 — you should see: *“CS101 is full (2/2 seats). No more students can enroll.”*

## Database schema

```
users          courses              enrollments
─────────      ─────────            ─────────────
id             id                   id
username       code (unique)        student_id → users
email          title                course_id → courses
password_hash  description          grade (nullable)
role           max_capacity         enrolled_at
               teacher_id → users   UNIQUE(student_id, course_id)
```

## Code comments (EN / 中文)

- **Python** (`app.py`, `database.py`): `# EN:` / `# ZH:` on imports, routes, and logic
- **CSS / JS**: `/* EN: */` block comments and `/** */` in `app.js`
- **HTML templates**: `{# EN: ... ZH: ... #}` at the top of each file
- **Templates detail**: see `docs/CODE_ANNOTATIONS.md` for section-by-section bilingual notes

## Project structure (Flask)

This project uses **`database.py`** for SQLite (no separate `models.py` — no SQLAlchemy ORM).

```
full-stack-study-system/
├── app.py                    # Flask app: routes, login, enroll, teacher CRUD
├── database.py               # DB connection, tables, demo seed data
├── requirements.txt          # Flask, Werkzeug
├── .gitignore
├── README.md
├── docs/
│   └── CODE_ANNOTATIONS.md   # Bilingual notes for HTML templates
├── static/
│   ├── css/style.css         # UI styles
│   └── js/app.js             # Confirm dialogs, flash auto-hide
└── templates/
    ├── base.html             # Layout, nav, flash messages
    ├── login.html
    ├── register.html
    ├── student/
    │   ├── courses.html      # Browse / enroll / drop
    │   ├── my_courses.html
    │   └── grades.html
    └── teacher/
        ├── courses.html      # List / delete courses
        ├── course_form.html  # Add / edit course
        └── students.html     # Grades / remove student
```

After clone, run `python app.py` — SQLite file `study_system.db` is created locally (not in git).

## Thesis alignment

This prototype matches the planned thesis scope: full-stack development, simple relational database design, authentication/authorization, and basic UX for a study-system scenario.
