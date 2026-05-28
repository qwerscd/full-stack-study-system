# Full-Stack Study System

Thesis prototype: **Design and Development of a Full-Stack Study System**  
Author: **Chen Junshuo**

A mini web application for course registration, enrollment management, and grades, with **student** and **teacher** roles.

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

## Project structure

```
study-system/
├── app.py              # Flask routes & business logic
├── database.py         # SQLite setup & seed data
├── docs/CODE_ANNOTATIONS.md  # Bilingual notes for HTML templates
├── requirements.txt
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/          # HTML pages
```

## Thesis alignment

This prototype matches the planned thesis scope: full-stack development, simple relational database design, authentication/authorization, and basic UX for a study-system scenario.
