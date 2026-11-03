from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Group, Student, Attendance
from app.auth import get_current_user
from datetime import date

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
def teacher_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "teacher": return RedirectResponse("/login", status_code=302)
    groups = db.query(Group).filter(Group.teacher_id == user.id).all()
    return templates.TemplateResponse("teacher_dashboard.html", {
        "request": request, "user": user, "groups": groups,
    })

@router.get("/group/{group_id}", response_class=HTMLResponse)
def teacher_group_attendance(group_id: int, request: Request, date_str: str = None, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "teacher": return RedirectResponse("/login", status_code=302)
    
    # Faqat o'z guruhini ko'ra oladi
    group = db.query(Group).filter(Group.id == group_id, Group.teacher_id == user.id).first()
    if not group: return RedirectResponse("/teacher/dashboard", status_code=302)
    
    target_date = date_str or date.today().isoformat()
    students = db.query(Student).filter(Student.group_id == group.id).all()
    
    existing = db.query(Attendance).filter(Attendance.date == target_date, Attendance.student_id.in_([s.id for s in students])).all()
    attendance_map = {a.student_id: a.status for a in existing}

    return templates.TemplateResponse("teacher_attendance.html", {
        "request": request, "user": user, "group": group, "students": students,
        "selected_date": target_date, "attendance_map": attendance_map
    })

@router.post("/group/{group_id}/mark")
async def teacher_mark_attendance(group_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "teacher": return RedirectResponse("/login", status_code=302)
    
    group = db.query(Group).filter(Group.id == group_id, Group.teacher_id == user.id).first()
    if not group: return RedirectResponse("/teacher/dashboard", status_code=302)

    form = await request.form()
    target_date = form.get("date_str") or date.today().isoformat()
    
    for key, value in form.items():
        if key.startswith("status_") and value:
            student_id = int(key.replace("status_", ""))
            existing = db.query(Attendance).filter(Attendance.student_id == student_id, Attendance.date == target_date).first()
            if existing: existing.status = value
            else: db.add(Attendance(student_id=student_id, date=target_date, status=value))
    db.commit()
    return RedirectResponse(f"/teacher/group/{group_id}?date_str={target_date}", status_code=302)
