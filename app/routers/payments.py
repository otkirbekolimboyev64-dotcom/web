from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, Payment
from app.auth import get_current_user
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def payments_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role not in ("admin", "teacher"):
        return RedirectResponse("/login", status_code=302)
    month = datetime.now().strftime("%Y-%m")
    payments = db.query(Payment).filter(Payment.month == month)\
                 .order_by(Payment.paid_at.desc()).all()
    students = db.query(Student).filter(Student.is_active == True).all()
    return templates.TemplateResponse("payments.html", {
        "request": request, "user": user,
        "payments": payments, "students": students,
        "current_month": month,
    })


@router.post("/new")
def payment_create(
    request: Request,
    student_id: int = Form(...),
    amount: float = Form(...),
    month: str = Form(...),
    status: str = Form("paid"),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user or user.role not in ("admin", "teacher"):
        return RedirectResponse("/login", status_code=302)
    db.add(Payment(
        student_id=student_id, amount=amount,
        month=month, status=status, note=note,
    ))
    db.commit()
    return RedirectResponse("/payments/", status_code=302)


@router.post("/{payment_id}/delete")
def payment_delete(payment_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "admin":
        return RedirectResponse("/login", status_code=302)
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if p:
        db.delete(p)
        db.commit()
    return RedirectResponse("/payments/", status_code=302)
