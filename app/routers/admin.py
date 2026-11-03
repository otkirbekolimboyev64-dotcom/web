from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, Course, User, Group
from app.auth import get_current_user, hash_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def _admin_only(request: Request):
    user = get_current_user(request)
    if not user or user.role != "admin":
        return None
    return user

# --- GURUHLAR (YANGI) ---
@router.get("/groups", response_class=HTMLResponse)
def groups_list(request: Request, db: Session = Depends(get_db)):
    user = _admin_only(request)
    if not user: return RedirectResponse("/login", status_code=302)
    groups = db.query(Group).all()
    courses = db.query(Course).all()
    teachers = db.query(User).filter(User.role == "teacher").all()
    return templates.TemplateResponse("groups.html", {
        "request": request, "user": user, "groups": groups, "courses": courses, "teachers": teachers,
    })

@router.post("/groups/new")
def group_create(
    request: Request, name: str = Form(...), course_id: int = Form(...),
    teacher_id: int = Form(None), db: Session = Depends(get_db),
):
    if not _admin_only(request): return RedirectResponse("/login", status_code=302)
    db.add(Group(name=name, course_id=course_id, teacher_id=teacher_id or None))
    db.commit()
    return RedirectResponse("/admin/groups", status_code=302)

# --- O'QUVCHILAR ---
@router.get("/students", response_class=HTMLResponse)
def students_list(request: Request, db: Session = Depends(get_db)):
    user = _admin_only(request)
    if not user: return RedirectResponse("/login", status_code=302)
    students = db.query(Student).order_by(Student.full_name).all()
    return templates.TemplateResponse("students.html", {
        "request": request, "user": user, "students": students,
    })

@router.get("/students/new", response_class=HTMLResponse)
def student_new(request: Request, db: Session = Depends(get_db)):
    user = _admin_only(request)
    if not user: return RedirectResponse("/login", status_code=302)
    groups = db.query(Group).all()
    return templates.TemplateResponse("student_form.html", {
        "request": request, "user": user, "groups": groups, "student": None,
    })

@router.post("/students/new")
def student_create(
    request: Request, full_name: str = Form(...), phone: str = Form(""),
    parent_phone: str = Form(...), parent_name: str = Form(""),
    group_id: int = Form(...), monthly_fee: float = Form(...),
    telegram_id: str = Form(""), db: Session = Depends(get_db),
):
    if not _admin_only(request): return RedirectResponse("/login", status_code=302)
    db.add(Student(
        full_name=full_name, phone=phone, parent_phone=parent_phone, parent_name=parent_name,
        group_id=group_id, monthly_fee=monthly_fee, telegram_id=telegram_id or None,
    ))
    db.commit()
    return RedirectResponse("/admin/students", status_code=302)

@router.get("/students/{student_id}/edit", response_class=HTMLResponse)
def student_edit(student_id: int, request: Request, db: Session = Depends(get_db)):
    user = _admin_only(request)
    if not user: return RedirectResponse("/login", status_code=302)
    student = db.query(Student).filter(Student.id == student_id).first()
    groups = db.query(Group).all()
    return templates.TemplateResponse("student_form.html", {
        "request": request, "user": user, "groups": groups, "student": student,
    })

@router.post("/students/{student_id}/edit")
def student_update(
    student_id: int, request: Request, full_name: str = Form(...), phone: str = Form(""),
    parent_phone: str = Form(...), parent_name: str = Form(""),
    group_id: int = Form(...), monthly_fee: float = Form(...),
    telegram_id: str = Form(""), db: Session = Depends(get_db),
):
    if not _admin_only(request): return RedirectResponse("/login", status_code=302)
    student = db.query(Student).filter(Student.id == student_id).first()
    if student:
        student.full_name = full_name
        student.phone = phone
        student.parent_phone = parent_phone
        student.parent_name = parent_name
        student.group_id = group_id
        student.monthly_fee = monthly_fee
        student.telegram_id = telegram_id or None
        db.commit()
    return RedirectResponse("/admin/students", status_code=302)

@router.post("/students/{student_id}/delete")
def student_delete(student_id: int, request: Request, db: Session = Depends(get_db)):
    if not _admin_only(request): return RedirectResponse("/login", status_code=302)
    student = db.query(Student).filter(Student.id == student_id).first()
    if student: db.delete(student); db.commit()
    return RedirectResponse("/admin/students", status_code=302)

# --- KURSLAR ---
@router.get("/courses", response_class=HTMLResponse)
def courses_list(request: Request, db: Session = Depends(get_db)):
    user = _admin_only(request)
    if not user: return RedirectResponse("/login", status_code=302)
    courses = db.query(Course).all()
    return templates.TemplateResponse("courses.html", {
        "request": request, "user": user, "courses": courses,
    })

@router.post("/courses/new")
def course_create(request: Request, name: str = Form(...), price: float = Form(...), db: Session = Depends(get_db)):
    if not _admin_only(request): return RedirectResponse("/login", status_code=302)
    db.add(Course(name=name, price=price))
    db.commit()
    return RedirectResponse("/admin/courses", status_code=302)

# --- O'QITUVCHILAR ---
@router.get("/teachers", response_class=HTMLResponse)
def teachers_list(request: Request, db: Session = Depends(get_db)):
    user = _admin_only(request)
    if not user: return RedirectResponse("/login", status_code=302)
    teachers = db.query(User).filter(User.role == "teacher").all()
    return templates.TemplateResponse("teachers.html", {
        "request": request, "user": user, "teachers": teachers,
    })

@router.post("/teachers/new")
def teacher_create(request: Request, username: str = Form(...), password: str = Form(...), full_name: str = Form(...), db: Session = Depends(get_db)):
    if not _admin_only(request): return RedirectResponse("/login", status_code=302)
    if not db.query(User).filter(User.username == username).first():
        db.add(User(username=username, password=hash_password(password), full_name=full_name, role="teacher"))
        db.commit()
    return RedirectResponse("/admin/teachers", status_code=302)
