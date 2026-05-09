import asyncio
import logging
import os
from datetime import datetime, date

import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import Database

# ─── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Config ─────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "")
GROUP_ID    = int(os.getenv("GROUP_ID", "0"))          # Guruh chat_id (manfiy raqam)
ADMIN_IDS   = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
TIMEZONE    = pytz.timezone("Asia/Tashkent")           # UTC+5
REPORT_HOUR = 10                                        # Hisobot qabul qilish chegarasi (10:00)

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
        "📸 Har kuni soat <b>10:00 gacha</b> screenshot yuboring.\n"
        "📊 Soat 10:00 da natijalar e'lon qilinadi.",
        parse_mode="HTML",
    )


@dp.message(Command("status"))
async def cmd_status(message: Message):
    """Bugungi holat — kim topshirdi, kim topshirmadi."""
    today = date.today().isoformat()
    employees = db.get_all_employees()
    submitted, missing = [], []

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
    """Admin: xodim qo'shish.  /addemployee 123456789 Ism Familiya @username"""
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔ Siz admin emassiz.")

    parts = message.text.split(maxsplit=4)
    # /addemployee <user_id> <full_name> [username]
    if len(parts) < 3:
        return await message.answer(
            "Ishlatish: <code>/addemployee &lt;user_id&gt; Ism Familiya [@username]</code>",
            parse_mode="HTML",
        )

    try:
        user_id   = int(parts[1])
        full_name = parts[2]
        username  = parts[3].lstrip("@") if len(parts) > 3 else ""
    except (ValueError, IndexError):
        return await message.answer("❌ Noto'g'ri format.")

    db.add_employee(user_id, full_name, username)
    await message.answer(f"✅ <b>{full_name}</b> ro'yxatga qo'shildi.", parse_mode="HTML")


@dp.message(Command("removeemployee"))
async def cmd_remove_employee(message: Message):
    """Admin: xodimni o'chirish.  /removeemployee <user_id>"""
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔ Siz admin emassiz.")

    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer("Ishlatish: <code>/removeemployee &lt;user_id&gt;</code>", parse_mode="HTML")

    try:
        user_id = int(parts[1])
    except ValueError:
        return await message.answer("❌ user_id raqam bo'lishi kerak.")

    db.remove_employee(user_id)
    await message.answer(f"✅ ID {user_id} ro'yxatdan o'chirildi.")


@dp.message(Command("listemployees"))
async def cmd_list_employees(message: Message):
    """Admin: barcha xodimlar ro'yxati."""
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔ Siz admin emassiz.")

    employees = db.get_all_employees()
    if not employees:
        return await message.answer("Ro'yxat bo'sh.")

    text = "👥 <b>Xodimlar ro'yxati:</b>\n\n"
    for i, e in enumerate(employees, 1):
        uname = f"@{e['username']}" if e.get("username") else "—"
        text += f"{i}. <b>{e['full_name']}</b> | ID: <code>{e['user_id']}</code> | {uname}\n"

    await message.answer(text, parse_mode="HTML")


# ─── ASOSIY FUNKSIYA: rasm qabul qilish ─────────────────────────────────────

@dp.message(F.photo | F.text | F.document | F.video)
async def handle_photo(message: Message):
    """Guruhdan rasm kelsa, soat va whitelist tekshiruvi."""
    # Faqat belgilangan guruhdan
    if message.chat.id != GROUP_ID:
        return

    user_id = message.from_user.id

    # Xodimlar ro'yxatida bormi?
    if not db.is_employee(user_id):
        return

    # O'zbekiston vaqti
    now_uz = datetime.now(TIMEZONE)

    # Faqat 09:00 - 10:00 oralig'ida
    if now_uz.hour < 9:
        return

    if now_uz.hour >= REPORT_HOUR:
        return

    # Bugunmi?
    today = now_uz.date().isoformat()

    # Allaqachon topshirganmi?
    if db.get_last_report_date(user_id) == today:
        await message.reply("✅ Siz bugun allaqachon hisobot topshirgansiz!")
        return

    # Sana yangilash
    db.update_report(user_id, today)
    full_name = db.get_employee_name(user_id)
    await message.reply(f"✅ <b>{full_name}</b>, hisobotingiz qabul qilindi!", parse_mode="HTML")


# ════════════════════════════════════════════════════════════════════════════
#  SCHEDULER — Har kuni soat 10:00 da avtomatik xabar
# ════════════════════════════════════════════════════════════════════════════

async def send_daily_report():
    """Soat 10:00 da guruhga natija yuborish."""
    now_uz = datetime.now(TIMEZONE)

    # Dam olish kunlari (6=shanba, 0=yakshanba Python weekday() bo'yicha)
    if now_uz.weekday() in (5, 6):
        logger.info("Dam olish kuni — hisobot yuborilmadi.")
        return

    today      = now_uz.date().isoformat()
    employees  = db.get_all_employees()
    submitted  = [e for e in employees if e["last_report_date"] == today]
    missing    = [e for e in employees if e["last_report_date"] != today]

    text  = f"📊 <b>Bugungi hisobot natijalari ({today}):</b>\n\n"
    text += f"✅ <b>Topshirdi: {len(submitted)} kishi</b>\n"
    for e in submitted:
        text += f"  • {e['full_name']}\n"

    text += f"\n❌ <b>Topshirmadi: {len(missing)} kishi</b>\n"
    for i, e in enumerate(missing, 1):
        mention = f"@{e['username']}" if e.get("username") else e["full_name"]
        text += f"  {i}. {mention}\n"

    text += "\n<i>Eslatma: Hisobotlar har kuni 10:00 gacha qabul qilinadi.</i>"

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

    from datetime import datetime as dt
now = dt.now()
scheduler.add_job(
    send_daily_report,
    trigger="cron",
    hour=now.hour,
    minute=now.minute + 2,
)
    scheduler.start()
    logger.info(f"Scheduler ishga tushdi. Hisobot soat {REPORT_HOUR}:00 (Toshkent vaqti) da yuboriladi.")

    logger.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
