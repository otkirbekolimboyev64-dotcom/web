import asyncio
import os
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from datetime import datetime
from dotenv import load_dotenv

from app.database import SessionLocal
from app.models import Student, Payment

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def send_debt_reminders():
    db: Session = SessionLocal()
    bot = Bot(token=BOT_TOKEN)
    month = datetime.now().strftime("%Y-%m")
    try:
        students = db.query(Student).filter(
            Student.is_active == True, Student.telegram_id != None
        ).all()
        for s in students:
            payments = db.query(Payment).filter(
                Payment.student_id == s.id, Payment.month == month
            ).all()
            total_paid = sum(p.amount for p in payments if p.status == "paid")
            debt = s.monthly_fee - total_paid
            if debt > 0:
                try:
                    await bot.send_message(
                        int(s.telegram_id),
                        f"⚠️ Hurmatli ota-ona!\n\n"
                        f"<b>{s.full_name}</b> uchun {month} oyiga "
                        f"<b>{debt:,.0f} so'm</b> qarz mavjud.\n"
                        f"Iltimos, to'lovni amalga oshiring.",
                        parse_mode="HTML",
                    )
                except Exception as e:
                    print(f"Xabar yuborilmadi ({s.telegram_id}): {e}")
    finally:
        db.close()
        await bot.session.close()


async def run_scheduler():
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(send_debt_reminders, "cron", day=5, hour=10, minute=0)
    scheduler.start()
    print("📅 Scheduler ishga tushdi (har oy 5-sanasida 10:00)")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(run_scheduler())
