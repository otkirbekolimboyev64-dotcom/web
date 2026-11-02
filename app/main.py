import os
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from dotenv import load_dotenv

from app.database import engine, Base, get_db, SessionLocal
from app.models import User, Student, Course, Payment
from app.auth import create_session, get_current_user, hash_password, verify_password
from app.routers import admin, teacher, payments, attendance, reports

load_dotenv()
Base.metadata.create_all(bind=engine)


def create_default_admin():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.role == "admin").first():
            db.add(User(
                username=os.getenv("ADMIN_USERNAME", "admin"),
                password=hash_password(os.getenv("ADMIN_PASSWORD", "admin123")),
                full_name="Administrator",
                role="admin",
            ))
            db.commit()
    finally:
        db.close()


create_default_admin()

app = FastAPI(title="O'quv Markaz Boshqaruv Tizimi")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(teacher.router, prefix="/teacher", tags=["teacher"])
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Login yoki parol xato!"},
            status_code=401,
        )
    token = create_session(user.id)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie("session", token, httponly=True, max_age=60 * 60 * 24 * 7)
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session")
    return response


@app.get("/")
def root():
    return RedirectResponse("/dashboard", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    total_students = db.query(Student).filter(Student.is_active == True).count()
    total_courses = db.query(Course).count()
    current_month = datetime.now().strftime("%Y-%m")
    paid_count = db.query(Payment).filter(
        Payment.month == current_month, Payment.status == "paid"
    ).count()
    debt_count = db.query(Payment).filter(
        Payment.month == current_month, Payment.status == "debt"
    ).count()
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user": user,
        "total_students": total_students,
        "total_courses": total_courses,
        "paid_count": paid_count,
        "debt_count": debt_count,
        "current_month": current_month,
    })
