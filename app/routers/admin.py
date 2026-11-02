from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, Course, User
from app.auth import get_current_user, hash_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _admin_only(request: Request):
    user = get_current_user(request)
    if not user or user.role != "admin":
        return None
    return user


@router.get("/students", response_class=HTMLResponse)
def students_list(request: Request, db: Session = Depends(get_db)):
    user = _admin_only(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    students = db.query(Student).order_by(Student.full_name).all()
    return templates.TemplateResponse("students.html", {
        "request": request, "user": user, "students": students,
    })


@router.get("/students/new", response_class=HTMLResponse)
def student_new(request: Request, db: Session = Depends(get_db)):
    user = _admin_only(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    courses = db.query(Course).all()
    return templates.TemplateResponse("student_form.html", {
        "request": request, "user": user, "courses": courses, "student": None,
    })


@router.post("/students/new")
def student_create(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(""),
    parent_phone: str = Form(...),
    parent_name: str = Form(""),
    course_id: int = Form(...),
    group_name: str = Form(""),
    monthly_fee: float = Form(...),
    telegram_id: str = Form(""),
    db: Session = Depends(get_db),
):
    if not _admin_only(request):
        return RedirectResponse("/login", status_code=302)
    db.add(Student(
        full_name=full_name, phone=phone,
        parent_phone=parent_phone, parent_name=parent_name,
        course_id=course_id, group_name=group_name,
        monthly_fee=monthly_fee, telegram_id=telegram_id or None,
    ))
    db.commit()
    return RedirectResponse("/admin/students", status_code=302)


@router.get("/students/{student_id}/edit", response_class=HTMLResponse)
def student_edit(student_id: int, request: Request, db: Session = Depends(get_db)):
    user = _admin_only(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return RedirectResponse("/admin/students", status_code=302)
    courses = db.query(Course).all()
    return templates.TemplateResponse("student_form.html", {
        "request": request, "user": user,
        "courses": courses, "student": student,
    })


@router.post("/students/{student_id}/edit")
def student_update(
    student_id: int, request: Request,
    full_name: str = Form(...),
    phone: str = Form(""),
    parent_phone: str = Form(...),
    parent_name: str = Form(""),
    course_id: int = Form(...),
    group_name: str = Form(""),
    monthly_fee: float = Form(...),
    telegram_id: str = Form(""),
    db: Session = Depends(get_db),
):
    if not _admin_only(request):
        return RedirectResponse("/login", status_code=302)
    student = db.query(Student).filter(Student.id == student_id).first()
    if student:
        student.full_name = full_name
        student.phone = phone
        student.parent_phone = parent_phone
        student.parent_name = parent_name
        student.course_id = course_id
        student.group_name = group_name
        student.monthly_fee = monthly_fee
        student.telegram_id = telegram_id or None
        db.commit()
    return RedirectResponse("/admin/students", status_code=302)


@router.post("/students/{student_id}/delete")
def student_delete(student_id: int, request: Request, db: Session = Depends(get_db)):
    if not _admin_only(request):
        return RedirectResponse("/login", status_code=302)
    student = db.query(Student).filter(Student.id == student_id).first()
    if student:
        db.delete(student)
        db.commit()
    return RedirectResponse("/admin/students", status_code=302)


@router.get("/courses", response_class=HTMLResponse)
def courses_list(request: Request, db: Session = Depends(get_db)):
    user = _admin_only(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    courses = db.query(Course).all()
    teachers = db.query(User).filter(User.role == "teacher").all()
    return templates.TemplateResponse("courses.html", {
        "request": request, "user": user,
        "courses": courses, "teachers": teachers,
    })


@router.post("/courses/new")
def course_create(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    duration_months: int = Form(1),
    teacher_id: int = Form(None),
    db: Session = Depends(get_db),
):
    if not _admin_only(request):
        return RedirectResponse("/login", status_code=302)
    db.add(Course(
        name=name, price=price,
        duration_months=duration_months,
        teacher_id=teacher_id or None,
    ))
    db.commit()
    return RedirectResponse("/admin/courses", status_code=302)


@router.post("/courses/{course_id}/delete")
def course_delete(course_id: int, request: Request, db: Session = Depends(get_db)):
    if not _admin_only(request):
        return RedirectResponse("/login", status_code=302)
    c = db.query(Course).filter(Course.id == course_id).first()
    if c:
        db.delete(c)
        db.commit()
    return RedirectResponse("/admin/courses", status_code=302)


@router.get("/teachers", response_class=HTMLResponse)
def teachers_list(request: Request, db: Session = Depends(get_db)):
    user = _admin_only(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    teachers = db.query(User).filter(User.role == "teacher").all()
    return templates.TemplateResponse("teachers.html", {
        "request": request, "user": user, "teachers": teachers,
    })


@router.post("/teachers/new")
def teacher_create(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    phone: str = Form(""),
    db: Session = Depends(get_db),
):
    if not _admin_only(request):
        return RedirectResponse("/login", status_code=302)
    if db.query(User).filter(User.username == username).first():
        return RedirectResponse("/admin/teachers", status_code=302)
    db.add(User(
        username=username, password=hash_password(password),
        full_name=full_name, role="teacher", phone=phone,
    ))
    db.commit()
    return RedirectResponse("/admin/teachers", status_code=302)


@router.post("/teachers/{teacher_id}/delete")
def teacher_delete(teacher_id: int, request: Request, db: Session = Depends(get_db)):
    if not _admin_only(request):
        return RedirectResponse("/login", status_code=302)
    t = db.query(User).filter(User.id == teacher_id, User.role == "teacher").first()
    if t:
        db.delete(t)
        db.commit()
    return RedirectResponse("/admin/teachers", status_code=302)
