import asyncio
import logging
import os
from datetime import datetime, date

import pytz
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import Database

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Config ─────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "")
GROUP_ID    = int(os.getenv("GROUP_ID", "0"))
ADMIN_IDS   = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
TIMEZONE    = pytz.timezone("Asia/Tashkent")
REPORT_HOUR = 10

# ─── Init ────────────────────────────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()
db  = Database("reports.db")


# ════════════════════════════════════════════════════════════════════════════
#  HANDLERS
# ════════════════════════════════════════════════════════════════════════════

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Salom! Men hisobot botiman.\n\n"
        "📸 Har kuni soat <b>09:00 dan 10:00 gacha</b> xabar yuboring.\n"
        "📊 Soat 10:00 da natijalar e'lon qilinadi.",
        parse_mode="HTML",
    )


@dp.message(Command("status"))
async def cmd_status(message: Message):
    today = date.today().isoformat()
    employees = db.get_all_employees()
    submitted = []
    missing = []

    for emp in employees:
        if emp["last_report_date"] == today:
            submitted.append(emp)
        else:
            missing.append(emp)

    text = f"📊 <b>Bugungi holat ({today}):</b>\n\n"
    text += f"✅ <b>Topshirdi ({len(submitted)} kishi):</b>\n"
    for e in submitted:
        text += f"  • {e['full_name']}\n"

    text += f"\n❌ <b>Topshirmadi ({len(missing)} kishi):</b>\n"
    for e in missing:
        mention = f"@{e['username']}" if e.get("username") else e["full_name"]
        text += f"  • {mention}\n"

    await message.answer(text or "Xodimlar ro'yxati bo'sh.", parse_mode="HTML")


@dp.message(Command("addemployee"))
async def cmd_add_employee(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Siz admin emassiz.")
        return

    parts = message.text.split(maxsplit=4)
    if len(parts) < 3:
        await message.answer(
            "Ishlatish: <code>/addemployee &lt;user_id&gt; Ism Familiya [@username]</code>",
            parse_mode="HTML",
        )
        return

    try:
        user_id   = int(parts[1])
        full_name = parts[2]
        username  = parts[3].lstrip("@") if len(parts) > 3 else ""
    except (ValueError, IndexError):
        await message.answer("❌ Noto'g'ri format.")
        return

    db.add_employee(user_id, full_name, username)
    await message.answer(f"✅ <b>{full_name}</b> ro'yxatga qo'shildi.", parse_mode="HTML")


@dp.message(Command("removeemployee"))
async def cmd_remove_employee(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Siz admin emassiz.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Ishlatish: <code>/removeemployee &lt;user_id&gt;</code>", parse_mode="HTML")
        return

    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ user_id raqam bo'lishi kerak.")
        return

    db.remove_employee(user_id)
    await message.answer(f"✅ ID {user_id} ro'yxatdan o'chirildi.")


@dp.message(Command("listemployees"))
async def cmd_list_employees(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Siz admin emassiz.")
        return

    employees = db.get_all_employees()
    if not employees:
        await message.answer("Ro'yxat bo'sh.")
        return

    text = "👥 <b>Xodimlar ro'yxati:</b>\n\n"
    for i, e in enumerate(employees, 1):
        uname = f"@{e['username']}" if e.get("username") else "—"
        text += f"{i}. <b>{e['full_name']}</b> | ID: <code>{e['user_id']}</code> | {uname}\n"

    await message.answer(text, parse_mode="HTML")


# ─── ASOSIY FUNKSIYA ─────────────────────────────────────────────────────────

@dp.message(F.photo | F.text | F.document | F.video)
async def handle_message(message: Message):
    if message.chat.id != GROUP_ID:
        return

    user_id = message.from_user.id

    if not db.is_employee(user_id):
        return

    now_uz = datetime.now(TIMEZONE)

    if now_uz.hour < 9:
        return

    if now_uz.hour >= REPORT_HOUR:
        return

    today = now_uz.date().isoformat()

    if db.get_last_report_date(user_id) == today:
        await message.reply("✅ Siz bugun allaqachon hisobot topshirgansiz!")
        return

    db.update_report(user_id, today)
    full_name = db.get_employee_name(user_id)
    await message.reply(f"✅ <b>{full_name}</b>, hisobotingiz qabul qilindi!", parse_mode="HTML")


# ════════════════════════════════════════════════════════════════════════════
#  SCHEDULER
# ════════════════════════════════════════════════════════════════════════════

async def send_daily_report():
    now_uz = datetime.now(TIMEZONE)

    if now_uz.weekday() in (5, 6):
        logger.info("Dam olish kuni — hisobot yuborilmadi.")
        return

    today     = now_uz.date().isoformat()
    employees = db.get_all_employees()
    submitted = [e for e in employees if e["last_report_date"] == today]
    missing   = [e for e in employees if e["last_report_date"] != today]

    text  = f"📊 <b>Bugungi hisobot natijalari ({today}):</b>\n\n"
    text += f"✅ <b>Topshirdi: {len(submitted)} kishi</b>\n"
    for e in submitted:
        text += f"  • {e['full_name']}\n"

    text += f"\n❌ <b>Topshirmadi: {len(missing)} kishi</b>\n"
    for i, e in enumerate(missing, 1):
        mention = f"@{e['username']}" if e.get("username") else e["full_name"]
        text += f"  {i}. {mention}\n"

    text += "\n<i>Eslatma: Hisobotlar har kuni 09:00 dan 10:00 gacha qabul qilinadi.</i>"

    try:
        await bot.send_message(GROUP_ID, text, parse_mode="HTML")
        logger.info("Kunlik hisobot yuborildi.")
    except Exception as e:
        logger.error(f"Xabar yuborishda xato: {e}")


# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

async def main():
    db.init()

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        send_daily_report,
        trigger="cron",
        hour=REPORT_HOUR,
        minute=0,
    )
    scheduler.start()
    logger.info(f"Scheduler ishga tushdi. Hisobot soat {REPORT_HOUR}:00 da yuboriladi.")

    logger.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
