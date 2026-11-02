from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Course
from app.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/courses", response_class=HTMLResponse)
def my_courses(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "teacher":
        return RedirectResponse("/login", status_code=302)
    courses = db.query(Course).filter(Course.teacher_id == user.id).all()
    return templates.TemplateResponse("courses.html", {
        "request": request, "user": user,
        "courses": courses, "teachers": [],
        "readonly": True,
    })
