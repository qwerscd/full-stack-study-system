# =============================================================================
# app.py — Flask 主应用 / Main Flask application
# EN: HTTP routes, login, student enroll/drop, teacher course management.
# ZH: HTTP 路由、登录、学生选课退课、教师课程管理。
# Author 作者: Chen Junshuo
# =============================================================================

from functools import wraps  # EN: Preserve function names in decorators / ZH: 装饰器保留原函数名

from flask import (  # EN: Flask web framework / ZH: Flask Web 框架
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash  # EN: Password hash verify/create / ZH: 密码校验与哈希

from database import db_session, get_connection, init_db, seed_demo_data  # EN: DB helpers / ZH: 数据库工具

app = Flask(__name__)  # EN: Create Flask app instance / ZH: 创建 Flask 应用实例
app.secret_key = "study-system-dev-key-change-in-production"  # EN: Session signing key (change in prod) / ZH: 会话密钥（生产环境请修改）


def get_db():
    """EN: One DB connection per request on Flask `g`. ZH: 每个请求在 g 上复用一条连接。"""
    if "db" not in g:  # EN: Reuse if already opened / ZH: 若尚未打开则创建
        g.db = get_connection()
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    """EN: Close DB when request ends. ZH: 请求结束时关闭数据库连接。"""
    db = g.pop("db", None)  # EN: Remove from g and get connection / ZH: 从 g 取出连接
    if db is not None:
        db.close()


def login_required(role=None):
    """
    EN: Decorator — must be logged in; optional role ('student' or 'teacher').
    ZH: 装饰器 — 必须已登录；可选限制角色（student 或 teacher）。
    """
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user_id = session.get("user_id")  # EN: Read user id from session cookie / ZH: 从会话读取用户 ID
            if not user_id:
                flash("Please log in first.", "warning")  # EN: Not logged in / ZH: 未登录提示
                return redirect(url_for("login"))

            user = get_db().execute(
                "SELECT id, username, role FROM users WHERE id = ?", (user_id,)
            ).fetchone()  # EN: Load user from DB / ZH: 从数据库加载用户
            if not user:
                session.clear()  # EN: Invalid session / ZH: 清除无效会话
                flash("Session expired. Please log in again.", "warning")
                return redirect(url_for("login"))

            if role and user["role"] != role:  # EN: Role mismatch / ZH: 角色不匹配
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("dashboard"))

            g.current_user = user  # EN: Available in route handlers / ZH: 供路由函数使用
            return view(*args, **kwargs)

        return wrapped

    return decorator


@app.route("/")
def index():
    """EN: Home — go to dashboard or login. ZH: 首页 — 已登录进仪表盘，否则进登录页。"""
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """EN: Login page and form handler. ZH: 登录页与表单处理。"""
    if request.method == "POST":  # EN: Form submitted / ZH: 用户提交表单
        username = request.form.get("username", "").strip()  # EN: Trim spaces / ZH: 去掉首尾空格
        password = request.form.get("password", "")

        user = get_db().execute(
            "SELECT id, username, role, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()  # EN: Find user by username / ZH: 按用户名查询

        if user and check_password_hash(user["password_hash"], password):  # EN: Verify password / ZH: 校验密码
            session.clear()  # EN: Fresh session / ZH: 清空旧会话
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]  # EN: Store role for nav / ZH: 保存角色用于导航
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")  # EN: Login failed / ZH: 登录失败

    return render_template("login.html")  # EN: Show login form (GET) / ZH: 显示登录页


@app.route("/register", methods=["GET", "POST"])
def register():
    """EN: Register new student or teacher. ZH: 注册新学生或教师账号。"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()  # EN: Normalize email / ZH: 邮箱转小写
        password = request.form.get("password", "")
        role = request.form.get("role", "student")  # EN: Default student / ZH: 默认学生

        if role not in ("student", "teacher"):  # EN: Validate role / ZH: 校验角色合法
            flash("Invalid role selected.", "danger")
            return render_template("register.html")

        if len(username) < 3 or len(password) < 6:  # EN: Minimum length rules / ZH: 最短长度规则
            flash("Username must be at least 3 characters and password at least 6.", "danger")
            return render_template("register.html")

        try:
            with db_session() as conn:
                conn.execute(
                    """
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (?, ?, ?, ?)
                    """,
                    (username, email, generate_password_hash(password), role),  # EN: Store hash not plain pwd / ZH: 存哈希不存明文
                )
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except Exception:  # EN: UNIQUE constraint on username/email / ZH: 用户名或邮箱重复
            flash("Username or email already exists.", "danger")

    return render_template("register.html")


@app.route("/logout")
def logout():
    """EN: Clear session and logout. ZH: 清除会话并退出登录。"""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required()
def dashboard():
    """EN: Route user to student or teacher home. ZH: 按角色跳转到对应首页。"""
    if g.current_user["role"] == "teacher":
        return redirect(url_for("teacher_courses"))
    return redirect(url_for("student_courses"))


@app.route("/student/courses")
@login_required(role="student")
def student_courses():
    """EN: Browse all courses with enroll status. ZH: 浏览所有课程及是否已选。"""
    db = get_db()
    courses = db.execute(
        """
        SELECT c.*, u.username AS teacher_name,
               (SELECT COUNT(*) FROM enrollments e WHERE e.course_id = c.id) AS enrolled_count,
               EXISTS(
                   SELECT 1 FROM enrollments e
                   WHERE e.course_id = c.id AND e.student_id = ?
               ) AS is_enrolled
        FROM courses c
        JOIN users u ON u.id = c.teacher_id
        ORDER BY c.code
        """,
        (g.current_user["id"],),  # EN: For is_enrolled subquery / ZH: 用于判断是否已选
    ).fetchall()
    return render_template("student/courses.html", courses=courses)


@app.route("/student/my-courses")
@login_required(role="student")
def student_my_courses():
    """EN: List courses this student enrolled in. ZH: 列出学生已选课程。"""
    courses = get_db().execute(
        """
        SELECT c.id AS course_id, c.code, c.title, c.description,
               u.username AS teacher_name, e.grade, e.enrolled_at
        FROM enrollments e
        JOIN courses c ON c.id = e.course_id
        JOIN users u ON u.id = c.teacher_id
        WHERE e.student_id = ?
        ORDER BY e.enrolled_at DESC
        """,
        (g.current_user["id"],),
    ).fetchall()
    return render_template("student/my_courses.html", courses=courses)


@app.route("/student/grades")
@login_required(role="student")
def student_grades():
    """EN: View grades for enrolled courses. ZH: 查看已选课程成绩。"""
    grades = get_db().execute(
        """
        SELECT c.code, c.title, e.grade, e.enrolled_at
        FROM enrollments e
        JOIN courses c ON c.id = e.course_id
        WHERE e.student_id = ?
        ORDER BY c.code
        """,
        (g.current_user["id"],),
    ).fetchall()
    return render_template("student/grades.html", grades=grades)


@app.route("/student/enroll/<int:course_id>", methods=["POST"])
@login_required(role="student")
def enroll_course(course_id):
    """EN: Enroll student if not duplicate and not full. ZH: 选课（防重复、防超员）。"""
    db = get_db()
    course = db.execute(
        "SELECT id, code, title, max_capacity FROM courses WHERE id = ?", (course_id,)
    ).fetchone()  # EN: Load course and capacity / ZH: 加载课程与容量

    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("student_courses"))

    existing = db.execute(
        "SELECT id FROM enrollments WHERE student_id = ? AND course_id = ?",
        (g.current_user["id"], course_id),
    ).fetchone()  # EN: Rule — no duplicate enrollment / ZH: 规则 — 禁止重复选课
    if existing:
        flash(f"You are already enrolled in {course['code']}.", "warning")
        return redirect(url_for("student_courses"))

    count = db.execute(
        "SELECT COUNT(*) AS cnt FROM enrollments WHERE course_id = ?", (course_id,)
    ).fetchone()["cnt"]  # EN: Current enrollment count / ZH: 当前已选人数
    if count >= course["max_capacity"]:  # EN: Rule — course full / ZH: 规则 — 课程已满
        flash(
            f"{course['code']} is full ({count}/{course['max_capacity']} seats). "
            "No more students can enroll.",
            "danger",
        )
        return redirect(url_for("student_courses"))

    with db_session() as conn:
        conn.execute(
            "INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)",
            (g.current_user["id"], course_id),
        )  # EN: Create enrollment row / ZH: 插入选课记录

    flash(f"Successfully enrolled in {course['title']}.", "success")
    return redirect(url_for("student_courses"))


@app.route("/student/drop/<int:course_id>", methods=["POST"])
@login_required(role="student")
def drop_course(course_id):
    """EN: Student drops (unenrolls from) a course. ZH: 学生退课。"""
    db = get_db()
    course = db.execute(
        "SELECT id, code, title FROM courses WHERE id = ?", (course_id,)
    ).fetchone()
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("student_my_courses"))

    enrollment = db.execute(
        """
        SELECT id FROM enrollments
        WHERE student_id = ? AND course_id = ?
        """,
        (g.current_user["id"], course_id),
    ).fetchone()  # EN: Must be enrolled to drop / ZH: 必须已选才能退课
    if not enrollment:
        flash(f"You are not enrolled in {course['code']}.", "warning")
        return redirect(url_for("student_courses"))

    with db_session() as conn:
        conn.execute(
            "DELETE FROM enrollments WHERE student_id = ? AND course_id = ?",
            (g.current_user["id"], course_id),
        )  # EN: Remove enrollment / ZH: 删除选课记录

    flash(f"Dropped {course['code']} — {course['title']}.", "success")
    next_page = request.args.get("next", "my_courses")  # EN: Return to browse or my-courses / ZH: 返回浏览页或我的课程
    if next_page == "browse":
        return redirect(url_for("student_courses"))
    return redirect(url_for("student_my_courses"))


@app.route("/teacher/courses")
@login_required(role="teacher")
def teacher_courses():
    """EN: List courses owned by this teacher. ZH: 列出该教师负责的课程。"""
    courses = get_db().execute(
        """
        SELECT c.*,
               (SELECT COUNT(*) FROM enrollments e WHERE e.course_id = c.id) AS enrolled_count
        FROM courses c
        WHERE c.teacher_id = ?
        ORDER BY c.code
        """,
        (g.current_user["id"],),
    ).fetchall()
    return render_template("teacher/courses.html", courses=courses)


@app.route("/teacher/courses/new", methods=["GET", "POST"])
@login_required(role="teacher")
def teacher_course_new():
    """EN: Create a new course. ZH: 教师添加新课程。"""
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()  # EN: Uppercase course code / ZH: 课程代码转大写
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        try:
            max_capacity = int(request.form.get("max_capacity", 30))  # EN: Max seats / ZH: 最大人数
        except ValueError:
            max_capacity = 0  # EN: Invalid number / ZH: 非法数字

        if not code or not title or max_capacity < 1:  # EN: Required fields / ZH: 必填校验
            flash("Please fill in code, title, and a valid capacity.", "danger")
            return render_template("teacher/course_form.html", course=None)

        try:
            with db_session() as conn:
                conn.execute(
                    """
                    INSERT INTO courses (code, title, description, max_capacity, teacher_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (code, title, description, max_capacity, g.current_user["id"]),  # EN: teacher_id = owner / ZH: 绑定当前教师
                )
            flash(f"Course {code} created.", "success")
            return redirect(url_for("teacher_courses"))
        except Exception:  # EN: Duplicate code UNIQUE / ZH: 课程代码重复
            flash("Course code already exists.", "danger")

    return render_template("teacher/course_form.html", course=None)


@app.route("/teacher/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required(role="teacher")
def teacher_course_edit(course_id):
    """EN: Edit own course only. ZH: 仅可编辑自己的课程。"""
    db = get_db()
    course = db.execute(
        "SELECT * FROM courses WHERE id = ? AND teacher_id = ?",
        (course_id, g.current_user["id"]),
    ).fetchone()  # EN: Ownership check / ZH: 所有权校验
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("teacher_courses"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        try:
            max_capacity = int(request.form.get("max_capacity", 30))
        except ValueError:
            max_capacity = 0

        if not title or max_capacity < 1:
            flash("Title and capacity are required.", "danger")
            return render_template("teacher/course_form.html", course=course)

        enrolled = db.execute(
            "SELECT COUNT(*) AS cnt FROM enrollments WHERE course_id = ?", (course_id,)
        ).fetchone()["cnt"]
        if max_capacity < enrolled:  # EN: Cannot shrink below current students / ZH: 容量不能小于已选人数
            flash(f"Capacity cannot be less than current enrollment ({enrolled}).", "danger")
            return render_template("teacher/course_form.html", course=course)

        with db_session() as conn:
            conn.execute(
                """
                UPDATE courses SET title = ?, description = ?, max_capacity = ?
                WHERE id = ?
                """,
                (title, description, max_capacity, course_id),
            )  # EN: Save course changes / ZH: 保存课程修改
        flash("Course updated.", "success")
        return redirect(url_for("teacher_courses"))

    return render_template("teacher/course_form.html", course=course)


@app.route("/teacher/courses/<int:course_id>/delete", methods=["POST"])
@login_required(role="teacher")
def teacher_course_delete(course_id):
    """EN: Delete own course; CASCADE removes enrollments. ZH: 删除自己的课程；选课记录级联删除。"""
    db = get_db()
    course = db.execute(
        "SELECT id, code, title FROM courses WHERE id = ? AND teacher_id = ?",
        (course_id, g.current_user["id"]),
    ).fetchone()
    if not course:
        flash("Course not found or you do not have permission to delete it.", "danger")
        return redirect(url_for("teacher_courses"))

    enrolled = db.execute(
        "SELECT COUNT(*) AS cnt FROM enrollments WHERE course_id = ?", (course_id,)
    ).fetchone()["cnt"]  # EN: Count for message / ZH: 统计人数用于提示

    with db_session() as conn:
        conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))  # EN: Delete course row / ZH: 删除课程

    if enrolled:
        flash(
            f"Course {course['code']} deleted. {enrolled} enrollment record(s) were removed.",
            "success",
        )
    else:
        flash(f"Course {course['code']} has been deleted.", "success")
    return redirect(url_for("teacher_courses"))


@app.route("/teacher/courses/<int:course_id>/students")
@login_required(role="teacher")
def teacher_course_students(course_id):
    """EN: View enrolled students for one course. ZH: 查看某课程的选课学生名单。"""
    db = get_db()
    course = db.execute(
        "SELECT * FROM courses WHERE id = ? AND teacher_id = ?",
        (course_id, g.current_user["id"]),
    ).fetchone()
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("teacher_courses"))

    students = db.execute(
        """
        SELECT e.id AS enrollment_id, u.username, u.email, e.grade, e.enrolled_at
        FROM enrollments e
        JOIN users u ON u.id = e.student_id
        WHERE e.course_id = ?
        ORDER BY u.username
        """,
        (course_id,),
    ).fetchall()
    return render_template(
        "teacher/students.html", course=course, students=students
    )


@app.route("/teacher/enrollments/<int:enrollment_id>/remove", methods=["POST"])
@login_required(role="teacher")
def teacher_remove_student(enrollment_id):
    """EN: Teacher removes a student from course. ZH: 教师将学生从课程中移除。"""
    row = get_db().execute(
        """
        SELECT e.id, u.username, c.id AS course_id, c.code, c.teacher_id
        FROM enrollments e
        JOIN users u ON u.id = e.student_id
        JOIN courses c ON c.id = e.course_id
        WHERE e.id = ?
        """,
        (enrollment_id,),
    ).fetchone()
    if not row or row["teacher_id"] != g.current_user["id"]:  # EN: Only course owner / ZH: 仅课程所属教师
        flash("Student enrollment not found.", "danger")
        return redirect(url_for("teacher_courses"))

    with db_session() as conn:
        conn.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))  # EN: Drop student / ZH: 移除选课

    flash(f"Removed {row['username']} from {row['code']}.", "success")
    return redirect(url_for("teacher_course_students", course_id=row["course_id"]))


@app.route("/teacher/grades/<int:enrollment_id>", methods=["POST"])
@login_required(role="teacher")
def update_grade(enrollment_id):
    """EN: Set or clear grade for one enrollment. ZH: 设置或清空某条选课的成绩。"""
    grade = request.form.get("grade", "").strip() or None  # EN: Empty → NULL / ZH: 空字符串视为无成绩
    db = get_db()
    row = db.execute(
        """
        SELECT e.id, c.id AS course_id, c.teacher_id, c.code
        FROM enrollments e
        JOIN courses c ON c.id = e.course_id
        WHERE e.id = ?
        """,
        (enrollment_id,),
    ).fetchone()
    if not row or row["teacher_id"] != g.current_user["id"]:
        flash("Enrollment not found.", "danger")
        return redirect(url_for("teacher_courses"))

    with db_session() as conn:
        conn.execute("UPDATE enrollments SET grade = ? WHERE id = ?", (grade, enrollment_id))

    flash(f"Grade updated for {row['code']}.", "success")
    return redirect(
        request.referrer or url_for("teacher_course_students", course_id=row["course_id"])
    )


if __name__ == "__main__":
    # EN: Run directly: python app.py / ZH: 直接运行：python app.py
    init_db()  # EN: Ensure tables exist / ZH: 确保表已创建
    seed_demo_data()  # EN: Load demo users/courses / ZH: 加载演示数据
    app.run(debug=True, host="127.0.0.1", port=5001)
