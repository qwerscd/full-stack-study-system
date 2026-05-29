# =============================================================================
# database.py — 数据库模块 / Database module
# 负责 SQLite 连接、表结构初始化、演示数据 / Handles SQLite, schema, demo data
# =============================================================================

import sqlite3  # EN: Python built-in SQLite driver / ZH: Python 内置 SQLite 驱动
from contextlib import contextmanager  # EN: Context manager for safe DB sessions / ZH: 上下文管理器，安全管理数据库会话
from pathlib import Path  # EN: Object-oriented file paths / ZH: 面向对象的路径处理

# EN: Database file path next to this script / ZH: 数据库文件路径（与本文件同目录）
DB_PATH = Path(__file__).parent / "study_system.db"


def get_connection():
    """EN: Open one SQLite connection. ZH: 打开一个 SQLite 连接。"""
    conn = sqlite3.connect(DB_PATH)  # EN: Connect to file / ZH: 连接到数据库文件
    conn.row_factory = sqlite3.Row  # EN: Rows behave like dicts (by column name) / ZH: 行可按列名访问
    conn.execute("PRAGMA foreign_keys = ON")  # EN: Enable FK constraints / ZH: 启用外键约束
    return conn  # EN: Return connection to caller / ZH: 返回连接对象


@contextmanager
def db_session():
    """
    EN: Context manager: auto commit on success, rollback on error, always close.
    ZH: 上下文管理器：成功则提交，出错则回滚，最后一定关闭连接。
    """
    conn = get_connection()  # EN: New connection / ZH: 新建连接
    try:
        yield conn  # EN: Hand connection to `with` block / ZH: 把连接交给 with 代码块使用
        conn.commit()  # EN: Save changes if no exception / ZH: 无异常则提交事务
    except Exception:
        conn.rollback()  # EN: Undo changes on failure / ZH: 失败时回滚
        raise  # EN: Re-raise error for caller / ZH: 继续向上抛出异常
    finally:
        conn.close()  # EN: Always release connection / ZH: 无论如何都关闭连接


def init_db():
    """EN: Create tables if they do not exist. ZH: 若表不存在则创建表结构。"""
    with db_session() as conn:  # EN: Use managed session / ZH: 使用托管会话
        conn.executescript(
            """
            -- EN: users table stores login accounts / ZH: users 表存储登录账号
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- EN: Auto ID / ZH: 自增主键
                username TEXT NOT NULL UNIQUE,         -- EN: Login name, unique / ZH: 用户名，唯一
                email TEXT NOT NULL UNIQUE,            -- EN: Email, unique / ZH: 邮箱，唯一
                password_hash TEXT NOT NULL,           -- EN: Hashed password / ZH: 密码哈希
                role TEXT NOT NULL CHECK (role IN ('student', 'teacher')),  -- EN: Role / ZH: 角色
                created_at TEXT NOT NULL DEFAULT (datetime('now'))  -- EN: Register time / ZH: 注册时间
            );

            -- EN: courses table / ZH: courses 课程表
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,             -- EN: Course code e.g. CS101 / ZH: 课程代码
                title TEXT NOT NULL,                   -- EN: Course title / ZH: 课程名称
                description TEXT NOT NULL DEFAULT '',  -- EN: Description / ZH: 课程简介
                max_capacity INTEGER NOT NULL DEFAULT 30,  -- EN: Max seats / ZH: 最大选课人数
                teacher_id INTEGER NOT NULL,           -- EN: Owner teacher / ZH: 授课教师 ID
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- EN: enrollments = student-course + grade / ZH: enrollments 选课与成绩
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,           -- EN: Student user id / ZH: 学生用户 ID
                course_id INTEGER NOT NULL,            -- EN: Course id / ZH: 课程 ID
                grade TEXT,                            -- EN: Grade or NULL / ZH: 成绩，可为空
                enrolled_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE (student_id, course_id)       -- EN: No duplicate enroll / ZH: 禁止重复选课
            );
            """
        )


def ensure_demo_users():
    """
    EN: Add demo users (e.g. student3) without wiping DB.
    ZH: 在不清空数据库的情况下补全演示账号（如 student3）。
    """
    from werkzeug.security import generate_password_hash  # EN: Hash passwords / ZH: 密码哈希工具

    # EN: List of (username, email, password, role) / ZH: 演示账号列表
    demo_users = [
        ("teacher1", "teacher1@study.edu", "teacher123", "teacher"),
        ("teacher2", "teacher2@study.edu", "teacher123", "teacher"),
        ("student1", "student1@study.edu", "student123", "student"),
        ("student2", "student2@study.edu", "student123", "student"),
        ("student3", "student3@study.edu", "student123", "student"),
    ]
    with db_session() as conn:
        for username, email, password, role in demo_users:  # EN: Loop each demo user / ZH: 遍历每个演示用户
            exists = conn.execute(
                "SELECT 1 FROM users WHERE username = ?", (username,)
            ).fetchone()  # EN: Check if username exists / ZH: 检查用户名是否已存在
            if not exists:  # EN: Insert only when missing / ZH: 仅当不存在时插入
                conn.execute(
                    """
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (?, ?, ?, ?)
                    """,
                    (username, email, generate_password_hash(password), role),
                )


def seed_demo_data():
    """
    EN: Fill initial teachers, students, courses. No pre-enrollments (demo enrolls manually).
    ZH: 填充教师、学生、课程。不预置选课记录（演示时手动选）。
    """
    from werkzeug.security import generate_password_hash

    with db_session() as conn:
        # EN: If DB already has users, only ensure demo accounts / ZH: 若已有用户则只补演示账号
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            ensure_demo_users()
            return

        # EN: Seed teachers / ZH: 插入演示教师
        teachers = [
            ("teacher1", "teacher1@study.edu", "teacher123", "Dr. Wang"),
            ("teacher2", "teacher2@study.edu", "teacher123", "Prof. Li"),
        ]
        for username, email, password, _ in teachers:
            conn.execute(
                """
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, 'teacher')
                """,
                (username, email, generate_password_hash(password)),
            )

        # EN: Seed students / ZH: 插入演示学生
        students = [
            ("student1", "student1@study.edu", "student123"),
            ("student2", "student2@study.edu", "student123"),
            ("student3", "student3@study.edu", "student123"),
        ]
        for username, email, password in students:
            conn.execute(
                """
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, 'student')
                """,
                (username, email, generate_password_hash(password)),
            )

        # EN: (code, title, desc, capacity, teacher_id) / ZH: 课程元组
        courses = [
            ("CS101", "Introduction to Programming", "Python basics and problem solving.", 2, 1),
            ("CS201", "Web Development", "HTML, CSS, JavaScript, and Flask.", 30, 1),
            ("DB301", "Database Systems", "Relational design, SQL, and normalization.", 25, 2),
            ("UX210", "User Experience Design", "UX principles and interface design.", 20, 2),
        ]
        for code, title, desc, cap, teacher_id in courses:
            conn.execute(
                """
                INSERT INTO courses (code, title, description, max_capacity, teacher_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (code, title, desc, cap, teacher_id),
            )
        # EN: No default enrollments — use student1/2/3 live during demo / ZH: 不插入默认选课
