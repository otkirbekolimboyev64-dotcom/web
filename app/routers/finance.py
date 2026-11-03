from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, Payment, Expense
from app.auth import get_current_user
from datetime import datetime, date
from sqlalchemy import func

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def finance_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "admin": return RedirectResponse("/login", status_code=302)

    current_month = datetime.now().strftime("%Y-%m")
    
    # Umumiy tushum
    total_income = db.query(func.sum(Payment.amount)).filter(Payment.status == "paid").scalar() or 0
    # Umumiy xarajat
    total_expense = db.query(func.sum(Expense.amount)).scalar() or 0
    # Sof foyda
    net_profit = total_income - total_expense

    # Qarzdorlar (joriy oy uchun to'lamaganlar)
    students = db.query(Student).filter(Student.is_active == True).all()
    debtors = []
    total_debt = 0
    for s in students:
        paid = db.query(func.sum(Payment.amount)).filter(Payment.student_id == s.id, Payment.month == current_month, Payment.status == "paid").scalar() or 0
        debt = s.monthly_fee - paid
        if debt > 0:
            debtors.append({"student": s, "debt": debt})
            total_debt += debt

    recent_payments = db.query(Payment).order_by(Payment.paid_at.desc()).limit(10).all()
    recent_expenses = db.query(Expense).order_by(Expense.date.desc()).limit(10).all()

    return templates.TemplateResponse("finance.html", {
        "request": request, "user": user,
        "total_income": total_income, "total_expense": total_expense, "net_profit": net_profit,
        "debtors": debtors, "total_debt": total_debt,
        "recent_payments": recent_payments, "recent_expenses": recent_expenses,
        "current_month": current_month
    })

@router.post("/expense/new")
def add_expense(request: Request, title: str = Form(...), amount: float = Form(...), date_str: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "admin": return RedirectResponse("/login", status_code=302)
    db.add(Expense(title=title, amount=amount, date=date_str))
    db.commit()
    return RedirectResponse("/finance/", status_code=302)

@router.post("/payment/new")
def add_payment(request: Request, student_id: int = Form(...), amount: float = Form(...), month: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "admin": return RedirectResponse("/login", status_code=302)
    db.add(Payment(student_id=student_id, amount=amount, month=month, status="paid"))
    db.commit()
    return RedirectResponse("/finance/", status_code=302)
