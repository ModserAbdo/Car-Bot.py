from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters
)
import sqlite3
import os

# ================== الإعدادات ==================
TOKEN = os.environ.get("8328705400:AAHvExlsI-fUTD4sL6NS2gp1yr38TGaoL2w")
ADMIN_ID = 7942621245  # ← ضع Telegram ID الخاص بك

DB_NAME = "cars.db"

# ================== قاعدة البيانات ==================
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS cars (
    plate TEXT PRIMARY KEY,
    location TEXT,
    photo_id TEXT
)
""")
conn.commit()

# ================== أدوات ==================
def is_admin(user_id):
    return user_id == ADMIN_ID

# ================== أوامر ==================
def start(update, context):
    update.message.reply_text(
        "🚗 مرحبًا بك في بوت البحث عن السيارات\n\n"
        "🔍 اكتب رقم السيارة للبحث\n\n"
        "👮‍♂️ أوامر المشرف:\n"
        "/add - إضافة سيارة\n"
        "/delete رقم - حذف سيارة\n"
        "/cancel - إلغاء العملية\n"
        "/count - عدد السيارات",
        parse_mode="Markdown"
    )

# ================== البحث ==================
def search_car(update, context):
    if context.user_data.get("step"):
        handle_add_steps(update, context)
        return

    plate = update.message.text.strip()

    c.execute("SELECT location, photo_id FROM cars WHERE plate=?", (plate,))
    row = c.fetchone()

    if row:
        location, photo_id = row
        update.message.reply_photo(
            photo=photo_id,
            caption=f"🚗 رقم السيارة: {plate}\n📍 الموقع: {location}"
        )
    else:
        update.message.reply_text("❌ لا توجد سيارة بهذه النمرة")

# ================== إضافة سيارة ==================
def add_car(update, context):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ هذا الأمر للمشرف فقط")
        return

    context.user_data["step"] = "plate"
    update.message.reply_text("➕ أرسل رقم السيارة", parse_mode="Markdown")

def handle_add_steps(update, context):
    step = context.user_data.get("step")

    if step == "plate":
        context.user_data["plate"] = update.message.text.strip()
        context.user_data["step"] = "location"
        update.message.reply_text("📍 أرسل مكان السيارة", parse_mode="Markdown")

    elif step == "location":
        context.user_data["location"] = update.message.text.strip()
        context.user_data["step"] = "photo"
        update.message.reply_text("📷 أرسل صورة السيارة")

    elif step == "photo" and update.message.photo:
        plate = context.user_data["plate"]
        location = context.user_data["location"]
        photo_id = update.message.photo[-1].file_id

        c.execute(
            "INSERT OR REPLACE INTO cars VALUES (?, ?, ?)",
            (plate, location, photo_id)
        )
        conn.commit()

        context.user_data.clear()
        update.message.reply_text("✅ تم حفظ السيارة بنجاح")

# ================== إلغاء العملية ==================
def cancel(update, context):
    context.user_data.clear()
    update.message.reply_text("❌ تم إلغاء العملية")

# ================== حذف سيارة ==================
def delete_car(update, context):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ هذا الأمر للمشرف فقط")
        return

    if not context.args:
        update.message.reply_text("❗ استخدم:\n/delete رقم_السيارة")
        return

    plate = context.args[0]

    c.execute("SELECT plate FROM cars WHERE plate=?", (plate,))
    if not c.fetchone():
        update.message.reply_text("❌ السيارة غير موجودة")
        return

    c.execute("DELETE FROM cars WHERE plate=?", (plate,))
    conn.commit()

    update.message.reply_text("🗑️ تم حذف السيارة بنجاح")

# ================== عدد السيارات ==================
def count_cars(update, context):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ هذا الأمر للمشرف فقط")
        return

    c.execute("SELECT COUNT(*) FROM cars")
    count = c.fetchone()[0]

    update.message.reply_text(f"📊 عدد السيارات المسجلة: {count}")

# ================== التشغيل ==================
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("add", add_car))
dp.add_handler(CommandHandler("delete", delete_car))
dp.add_handler(CommandHandler("cancel", cancel))
dp.add_handler(CommandHandler("count", count_cars))

dp.add_handler(MessageHandler(Filters.photo, handle_add_steps))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, search_car))

updater.start_polling()

updater.idle()
