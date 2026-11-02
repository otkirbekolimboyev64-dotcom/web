from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.orm import Session
from datetime import datetime, date
import os

from app.database import SessionLocal
from app.models import Student, Payment, Attendance, User
from bot.keyboards import main_menu, admin_menu

router = Router()

ADMIN_TG_ID = os.getenv("ADMIN_TELEGRAM_ID", "")


def _get_student(db: Session, tg_id: str):
    return db.query(Student).filter(Student.telegram_id == tg_id).first()


def _is_admin(tg_id: str) -> bool:
    return str(tg_id) == str(ADMIN_TG_ID)


def _fmt_money(amount: float) -> str:
    return f"{amount:,.0f}".replace(",", " ")


def _start_text():
    return (
        "🤖 <b>O'quv Markaz Bot</b>\n\n"
        "Quyidagi buyruqlardan foydalaning:\n\n"
        "💰 <b>Balans</b> — qarz va to'lovlar\n"
        "📅 <b>Davomat</b> — bu oy davomati\n"
        "💳 <b>To'lovlar</b> — to'lov tarixi\n"
        "📚 <b>Kurs</b> — kurs ma'lumotlari\n"
        "ℹ️ <b>Ma'lumot</b> — farzand haqida\n\n"
        "Yoki buyruqni yozing:\n"
        "/balans /davomat /tolov /kurs /info"
    )


@router.message(CommandStart())
@router.message(Command("help"))
async def start_handler(message: Message):
    tg_id = str(message.from_user.id)
    db: Session = SessionLocal()
    try:
        # Admin bo'lsa
        if _is_admin(tg_id):
            await message.answer(
                "👨‍💼 Salom, Admin!\n\n"
                "Siz quyidagi buyruqlardan foydalanishingiz mumkin:\n\n"
                "⚠️ /qarzdorlar — barcha qarzdorlar\n"
                "📢 /xabar &lt;matn&gt; — ota-onalarga xabar\n\n"
                "Yoki ota-ona sifatida foydalaning.",
                reply_markup=admin_menu(),
                parse_mode="HTML",
            )
            return

        student = _get_student(db, tg_id)
        if not student:
            await message.answer(
                f"Assalomu alaykum! 👋\n\n"
                f"Sizning Telegram ID: <code>{tg_id}</code>\n\n"
                f"Iltimos, bu ID ni o'quv markaz administratoriga yuboring.\n"
                f"Ular sizni farzandingizga bog'lashadi.",
                parse_mode="HTML",
            )
            return

        await message.answer(
            f"Assalomu alaykum, <b>{student.parent_name or 'ota-ona'}</b>! 👋\n\n"
            f"Farzandingiz: <b>{student.full_name}</b>\n\n"
            f"Quyidagi tugmalardan foydalaning yoki buyruqni yozing:",
            reply_markup=main_menu(),
            parse_mode="HTML",
        )
    finally:
        db.close()


# ============ BALANS ============
@router.message(Command("balans"))
@router.message(F.text == "💰 Balans")
async def balans_handler(message: Message):
    tg_id = str(message.from_user.id)
    db: Session = SessionLocal()
    try:
        student = _get_student(db, tg_id)
        if not student:
            await message.answer("❌ Siz ro'yxatdan o'tmagansiz.")
            return

        month = datetime.now().strftime("%Y-%m")
        payments = db.query(Payment).filter(
            Payment.student_id == student.id, Payment.month == month
        ).all()
        total_paid = sum(p.amount for p in payments if p.status == "paid")
        debt = student.monthly_fee - total_paid
        status = "✅ Qarz yo'q" if debt <= 0 else f"⚠️ Qarzdor"

        await message.answer(
            f"💰 <b>Balans</b> — {month}\n\n"
            f"👶 {student.full_name}\n"
            f"📚 {student.course.name if student.course else '-'}\n\n"
            f"📊 Oylik to'lov: <b>{_fmt_money(student.monthly_fee)} so'm</b>\n"
            f"✅ To'langan: <b>{_fmt_money(total_paid)} so'm</b>\n"
            f"💸 Qarz: <b>{_fmt_money(debt)} so'm</b>\n\n"
            f"{status}",
            parse_mode="HTML",
        )
    finally:
        db.close()


# ============ DAVOMAT ============
@router.message(Command("davomat"))
@router.message(F.text == "📅 Davomat")
async def davomat_handler(message: Message):
    tg_id = str(message.from_user.id)
    db: Session = SessionLocal()
    try:
        student = _get_student(db, tg_id)
        if not student:
            await message.answer("❌ Siz ro'yxatdan o'tmagansiz.")
            return

        month = datetime.now().strftime("%Y-%m")
        attends = db.query(Attendance).filter(
            Attendance.student_id == student.id,
            Attendance.date >= f"{month}-01",
            Attendance.date <= f"{month}-31",
        ).order_by(Attendance.date.desc()).all()

        if not attends:
            await message.answer(
                f"📅 <b>{month}</b> oyi davomati\n\n"
                f"Hozircha davomat belgilanmagan.",
                parse_mode="HTML",
            )
            return

        total = len(attends)
        present = sum(1 for a in attends if a.status == "present")
        late = sum(1 for a in attends if a.status == "late")
        absent = sum(1 for a in attends if a.status == "absent")
        excused = sum(1 for a in attends if a.status == "excused")

        icons = {"present": "✅", "late": "⏰", "absent": "❌", "excused": "📝"}
        labels = {"present": "Keldi", "late": "Kechikdi", "absent": "Kelmadi", "excused": "Sababli"}

        lines = [f"📅 <b>{month}</b> oyi davomati\n"]
        lines.append(f"👶 {student.full_name}\n")
        for a in attends[:10]:
            icon = icons.get(a.status, "•")
            label = labels.get(a.status, a.status)
            lines.append(f"{icon} {a.date.strftime('%d.%m')} — {label}")

        if len(attends) > 10:
            lines.append(f"\n... va yana {len(attends) - 10} ta kun")

        lines.append(
            f"\n\n📊 <b>Jami: {total} kun</b>\n"
            f"✅ Keldi: {present} | ⏰ Kechikdi: {late}\n"
            f"❌ Kelmadi: {absent} | 📝 Sababli: {excused}"
        )
        await message.answer("\n".join(lines), parse_mode="HTML")
    finally:
        db.close()


# ============ TO'LOVLAR ============
@router.message(Command("tolov"))
@router.message(Command("tolovlar"))
@router.message(F.text == "💳 To'lovlar")
async def tolov_handler(message: Message):
    tg_id = str(message.from_user.id)
    db: Session = SessionLocal()
    try:
        student = _get_student(db, tg_id)
        if not student:
            await message.answer("❌ Siz ro'yxatdan o'tmagansiz.")
            return

        payments = db.query(Payment).filter(
            Payment.student_id == student.id
        ).order_by(Payment.paid_at.desc()).limit(10).all()

        if not payments:
            await message.answer(
                f"💳 <b>To'lov tarixi</b>\n\n"
                f"Hozircha to'lov yo'q.",
                parse_mode="HTML",
            )
            return

        status_icon = {"paid": "✅", "partial": "⚠️", "debt": "❌"}
        lines = [f"💳 <b>To'lov tarixi</b>\n"]
        lines.append(f"👶 {student.full_name}\n")
        total = 0
        for p in payments:
            icon = status_icon.get(p.status, "•")
            lines.append(
                f"{icon} {p.paid_at.strftime('%d.%m.%Y')} — "
                f"<b>{_fmt_money(p.amount)} so'm</b> ({p.month})"
            )
            if p.status == "paid":
                total += p.amount
        lines.append(f"\n📊 Jami to'langan: <b>{_fmt_money(total)} so'm</b>")
        await message.answer("\n".join(lines), parse_mode="HTML")
    finally:
        db.close()


# ============ KURS ============
@router.message(Command("kurs"))
@router.message(F.text == "📚 Kurs")
async def kurs_handler(message: Message):
    tg_id = str(message.from_user.id)
    db: Session = SessionLocal()
    try:
        student = _get_student(db, tg_id)
        if not student:
            await message.answer("❌ Siz ro'yxatdan o'tmagansiz.")
            return

        course = student.course
        if not course:
            await message.answer("❌ Kurs biriktirilmagan.")
            return

        teacher = course.teacher.full_name if course.teacher else "—"
        await message.answer(
            f"📚 <b>Kurs ma'lumotlari</b>\n\n"
            f"📖 Nomi: <b>{course.name}</b>\n"
            f"💰 Narxi: <b>{_fmt_money(course.price)} so'm</b>\n"
            f"⏳ Davomiyligi: <b>{course.duration_months} oy</b>\n"
            f"👨‍🏫 O'qituvchi: <b>{teacher}</b>\n"
            f"👥 Guruh: <b>{student.group_name or '—'}</b>",
            parse_mode="HTML",
        )
    finally:
        db.close()


# ============ INFO ============
@router.message(Command("info"))
@router.message(Command("malumot"))
@router.message(F.text == "ℹ️ Ma'lumot")
async def info_handler(message: Message):
    tg_id = str(message.from_user.id)
    db: Session = SessionLocal()
    try:
        student = _get_student(db, tg_id)
        if not student:
            await message.answer("❌ Siz ro'yxatdan o'tmagansiz.")
            return

        await message.answer(
            f"ℹ️ <b>Farzand ma'lumotlari</b>\n\n"
            f"👶 F.I.Sh: <b>{student.full_name}</b>\n"
            f"📚 Kurs: <b>{student.course.name if student.course else '—'}</b>\n"
            f"👥 Guruh: <b>{student.group_name or '—'}</b>\n"
            f"📞 O'quvchi tel: <b>{student.phone or '—'}</b>\n"
            f"📞 Ota-ona tel: <b>{student.parent_phone}</b>\n"
            f"👤 Ota-ona: <b>{student.parent_name or '—'}</b>",
            parse_mode="HTML",
        )
    finally:
        db.close()


# ============ ADMIN: QARZDORLAR ============
@router.message(Command("qarzdorlar"))
@router.message(F.text == "⚠️ Qarzdorlar")
async def qarzdorlar_handler(message: Message):
    tg_id = str(message.from_user.id)
    if not _is_admin(tg_id):
        await message.answer("❌ Bu buyruq faqat admin uchun.")
        return

    db: Session = SessionLocal()
    try:
        month = datetime.now().strftime("%Y-%m")
        students = db.query(Student).filter(Student.is_active == True).all()
        debtors = []
        for s in students:
            payments = db.query(Payment).filter(
                Payment.student_id == s.id, Payment.month == month
            ).all()
            total_paid = sum(p.amount for p in payments if p.status == "paid")
            debt = s.monthly_fee - total_paid
            if debt > 0:
                debtors.append((s, debt))

        if not debtors:
            await message.answer(
                f"✅ <b>Qarzdorlar yo'q!</b>\n{month} — hamma to'lagan.",
                parse_mode="HTML",
            )
            return

        lines = [f"⚠️ <b>Qarzdorlar — {month}</b>\n"]
        total = 0
        for i, (s, debt) in enumerate(debtors, 1):
            lines.append(
                f"{i}. <b>{s.full_name}</b>\n"
                f"   📞 {s.parent_phone} | 💸 {_fmt_money(debt)} so'm"
            )
            total += debt
        lines.append(f"\n📊 Jami: <b>{_fmt_money(total)} so'm</b>")
        await message.answer("\n".join(lines), parse_mode="HTML")
    finally:
        db.close()


# ============ ADMIN: XABAR YUBORISH ============
@router.message(Command("xabar"))
async def xabar_handler(message: Message):
    tg_id = str(message.from_user.id)
    if not _is_admin(tg_id):
        await message.answer("❌ Bu buyruq faqat admin uchun.")
        return

    # /xabar <matn>
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "📢 <b>Xabar yuborish</b>\n\n"
            "Format:\n"
            "<code>/xabar Salom, ertaga dars yo'q!</code>\n\n"
            "Yoki tugmani bosing va matnni yozing.",
            parse_mode="HTML",
        )
        return

    text = parts[1]
    db: Session = SessionLocal()
    try:
        students = db.query(Student).filter(
            Student.is_active == True,
            Student.telegram_id != None,
            Student.telegram_id != "",
        ).all()

        sent = 0
        failed = 0
        for s in students:
            try:
                await message.bot.send_message(
                    int(s.telegram_id),
                    f"📢 <b>O'quv markaz xabari:</b>\n\n{text}",
                    parse_mode="HTML",
                )
                sent += 1
            except Exception as e:
                print(f"Xabar yuborilmadi ({s.telegram_id}): {e}")
                failed += 1

        await message.answer(
            f"✅ Xabar yuborildi!\n\n"
            f"📤 Yuborildi: <b>{sent}</b>\n"
            f"❌ Xato: <b>{failed}</b>",
            parse_mode="HTML",
        )
    finally:
        db.close()


# ============ NOMA'LUM BUYRUQ ============
@router.message(F.text & ~F.text.startswith("/"))
async def unknown_handler(message: Message):
    tg_id = str(message.from_user.id)
    db: Session = SessionLocal()
    try:
        student = _get_student(db, tg_id)
        if not student and not _is_admin(tg_id):
            await message.answer(
                f"Sizning Telegram ID: <code>{tg_id}</code>\n\n"
                f"Administratorga yuboring.",
                parse_mode="HTML",
            )
            return
        await message.answer(
            "🤔 Buyruq tushunarsiz.\n\n"
            "Menyudan foydalaning yoki /help yozing.",
        )
    finally:
        db.close()
