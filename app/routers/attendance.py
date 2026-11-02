from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, Attendance, Course
from app.auth import get_current_user
from datetime import date, datetime
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def attendance_page(
    request: Request,
    date_str: Optional[str] = None,
    course_id: Optional[str] = None,  # ✅ str, keyin konvert qilamiz
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user or user.role not in ("admin", "teacher"):
        return RedirectResponse("/login", status_code=302)

    target_date = date_str or date.today().isoformat()

    # course_id ni xavfsiz konvert qilish
    cid: Optional[int] = None
    if course_id and str(course_id).strip():
        try:
            cid = int(course_id)
        except (ValueError, TypeError):
            cid = None

    query = db.query(Student).filter(Student.is_active == True)
    if cid:
        query = query.filter(Student.course_id == cid)
    students = query.order_by(Student.full_name).all()

    existing = db.query(Attendance).filter(Attendance.date == target_date).all()
    attendance_map = {a.student_id: a.status for a in existing}

    courses = db.query(Course).all()

    return templates.TemplateResponse("attendance.html", {
        "request": request, "user": user,
        "students": students, "courses": courses,
        "selected_date": target_date,
        "attendance_map": attendance_map,
        "selected_course": cid,
    })


@router.post("/mark")
async def mark_attendance(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role not in ("admin", "teacher"):
        return RedirectResponse("/login", status_code=302)

    try:
        form = await request.form()
    except Exception as e:
        print(f"Form parse error: {e}")
        return RedirectResponse("/attendance/", status_code=302)

    target_date_raw = form.get("date_str")
    try:
        if target_date_raw:
            target_date = datetime.strptime(str(target_date_raw), "%Y-%m-%d").date()
        else:
            target_date = date.today()
    except ValueError:
        target_date = date.today()

    saved_count = 0
    for key, value in form.items():
        if key.startswith("status_") and value:
            try:
                student_id = int(str(key).replace("status_", ""))
            except (ValueError, AttributeError):
                continue

            existing = db.query(Attendance).filter(
                Attendance.student_id == student_id,
                Attendance.date == target_date,
            ).first()

            if existing:
                existing.status = str(value)
            else:
                db.add(Attendance(
                    student_id=student_id,
                    date=target_date,
                    status=str(value),
                ))
            saved_count += 1

    try:
        db.commit()
        print(f"✅ Davomat saqlandi: {saved_count} ta, sana: {target_date}")
    except Exception as e:
        db.rollback()
        print(f"❌ DB error: {e}")

    return RedirectResponse(
        f"/attendance/?date_str={target_date.isoformat()}",
        status_code=302,
    )
