# 代码中英文注释说明 / Bilingual Code Annotations

本文件补充 **HTML 模板** 的逐段说明。Python、CSS、JS 文件内已含 `# EN:` / `# ZH:` 或 `/* EN: */` 注释。

This file documents **HTML templates** section by section. Python, CSS, and JS use inline `# EN:` / `# ZH:` comments.

---

## templates/login.html

| 行 / Line | EN | ZH |
|-----------|----|----|
| form POST | Submit username/password to `/login` | 提交用户名密码到登录路由 |
| demo-hint | Show test accounts for thesis demo | 展示论文演示用测试账号 |

## templates/register.html

| EN | ZH |
|----|-----|
| Role select: student or teacher | 角色下拉：学生或教师 |
| POST creates user with hashed password | 提交后创建用户并存储密码哈希 |

## templates/student/courses.html

| EN | ZH |
|----|-----|
| Loop `courses` from SQL | 遍历后端查询的课程列表 |
| `full` = enrolled_count >= max_capacity | 已满 = 已选人数 ≥ 容量 |
| Enrolled → Drop form | 已选 → 显示退课表单 |
| Full → Try Enroll + notice | 已满 → 尝试选课按钮 + 英文满员说明 |

## templates/student/my_courses.html

| EN | ZH |
|----|-----|
| Table of student's enrollments | 表格显示学生已选课程 |
| Drop button per row | 每行退课按钮 |

## templates/student/grades.html

| EN | ZH |
|----|-----|
| Shows grade or "Not yet graded" | 显示成绩或“未评分” |

## templates/teacher/courses.html

| EN | ZH |
|----|-----|
| Lists only `teacher_id = current user` | 只列出当前教师的课程 |
| Delete POST → `teacher_course_delete` | 删除按钮提交到删除路由 |

## templates/teacher/course_form.html

| EN | ZH |
|----|-----|
| New: fields code, title, description, capacity | 新建：代码、标题、简介、容量 |
| Edit: code read-only | 编辑：课程代码不可改 |

## templates/teacher/students.html

| EN | ZH |
|----|-----|
| Grade form POST → `update_grade` | 成绩表单提交到更新成绩路由 |
| Remove POST → `teacher_remove_student` | 移除按钮提交到移除学生路由 |

---

Author 作者: **Chen Junshuo**
