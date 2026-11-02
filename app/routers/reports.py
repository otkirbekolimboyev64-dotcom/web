from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, Payment, Attendance
from app.auth import get_current_user
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _report_data(db: Session, month: str):
    students = db.query(Student).filter(Student.is_active == True).all()
    report = []
    for s in students:
        month_payments = db.query(Payment).filter(
            Payment.student_id == s.id, Payment.month == month
        ).all()
        total_paid = sum(p.amount for p in month_payments if p.status == "paid")
        attends = db.query(Attendance).filter(
            Attendance.student_id == s.id,
            Attendance.date >= f"{month}-01",
            Attendance.date <= f"{month}-31",
        ).all()
        total_days = len(attends)
        present_days = len([a for a in attends if a.status == "present"])
        pct = int(present_days / total_days * 100) if total_days else 0
        debt = s.monthly_fee - total_paid
        report.append({
            "student": s, "total_paid": total_paid, "debt": debt,
            "total_days": total_days, "present_days": present_days,
            "attendance_pct": pct,
            "status": "paid" if debt <= 0 else ("partial" if total_paid > 0 else "debt"),
        })
    return report


@router.get("/", response_class=HTMLResponse)
def reports_page(request: Request, month: str = None, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role not in ("admin", "teacher"):
        return RedirectResponse("/login", status_code=302)
    current_month = month or datetime.now().strftime("%Y-%m")
    data = _report_data(db, current_month)
    return templates.TemplateResponse("reports.html", {
        "request": request, "user": user,
        "report": data, "current_month": current_month,
    })


@router.get("/excel")
def export_excel(month: str = None, db: Session = Depends(get_db)):
    current_month = month or datetime.now().strftime("%Y-%m")
    data = _report_data(db, current_month)
    wb = Workbook()
    ws = wb.active
    ws.title = f"Hisobot {current_month}"
    ws.append([
        "O'quvchi", "Kurs", "Guruh", "To'langan (so'm)",
        "Qarz (so'm)", "Jami kun", "Kelgan kun", "Davomat %", "Holat",
    ])
    status_uz = {"paid": "To'langan", "partial": "Qismiy", "debt": "Qarzdor"}
    for r in data:
        ws.append([
            r["student"].full_name,
            r["student"].course.name if r["student"].course else "",
            r["student"].group_name or "",
            r["total_paid"], r["debt"],
            r["total_days"], r["present_days"],
            f"{r['attendance_pct']}%",
            status_uz.get(r["status"], ""),
        ])
    for col in ws.columns:
        max_len = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    return StreamingResponse(
        out,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=hisobot_{current_month}.xlsx"},
    )
