# Full-Stack Study System

Course project for my thesis (*Design and Development of a Full-Stack Study System*).  
Author: Chen Junshuo

It's a small web app where students can log in, pick courses, and check grades. Teachers can add courses and manage who enrolled.

GitHub: https://github.com/qwerscd/full-stack-study-system

## What I used

- HTML / CSS / JavaScript for the pages
- Python + Flask for the server
- SQLite for the database (file `study_system.db`, created when you first run the app)

There is no `models.py` — I put SQL and table setup in `database.py` because our course project didn't need ORM.

## Main functions

Students can register, log in, browse courses, enroll, drop a course, and see grades.

Teachers can create / edit / delete their own courses, see the student list, enter grades, and remove a student from a course.

Rules I implemented:

1. Each course has a max number of students. When it's full, nobody else can enroll.
2. The same student cannot enroll in the same course twice (checked in code + `UNIQUE` in the database).
3. Students and teachers see different pages (`student` vs `teacher` role).

## How to run

```bash
cd /Users/chenjunshuo/Projects/study-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5001** in the browser.

## Test accounts

| Role    | Username   | Password     |
|---------|------------|--------------|
| Student | student1   | student123   |
| Student | student2   | student123   |
| Student | student3   | student123   |
| Teacher | teacher1   | teacher123   |
| Teacher | teacher2   | teacher123   |

## Demo: course full (CS101)

CS101 is set to **2** seats only, so I can show the "full" message in class.

Steps I use when presenting:

1. **student1** logs in → Browse Courses → enroll **CS101** (now 1/2).
2. **student2** logs in → enroll **CS101** again (now 2/2, full).
3. **student3** logs in → Browse Courses → click **Try Enroll** on CS101 → should get:  
   `CS101 is full (2/2 seats). No more students can enroll.`

Nothing is pre-selected in the database anymore — I do all three steps live.

## Database (3 tables)

- `users` — login, role (`student` or `teacher`)
- `courses` — code, title, teacher, `max_capacity`
- `enrollments` — which student picked which course, optional `grade`

## Folder layout

```
app.py              # routes (login, enroll, teacher stuff)
database.py         # SQLite tables + demo users/courses
requirements.txt
static/css/style.css
static/js/app.js
templates/          # HTML pages (student + teacher)
```
