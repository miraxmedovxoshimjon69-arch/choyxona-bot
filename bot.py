import json
import logging
from datetime import datetime
from pathlib import Path

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.WARNING)

BASE = Path(__file__).parent
TOKEN_FILE = BASE / "token.txt"
ADMIN_FILE = BASE / "admin_id.txt"
ORDERS_FILE = BASE / "orders.json"
DOCS = BASE / "docs"
MENU_FILE = DOCS / "menu.json"
PHOTO_DIR = DOCS / "rasmlar"
PHOTO_DIR.mkdir(parents=True, exist_ok=True)

# GitHub Pages manzili: https://FOYDALANUVCHI.github.io/REPO/
WEBAPP_URL = "https://miraxmedovxoshimjon69-arch.github.io/choyxona-bot/"

ADDRESS_TEXT = "📍 Manzilimiz haqida ma’lumot tez orada qo‘shiladi."
CONTACT_TEXT = "☎️ Bog‘lanish uchun telefon raqami tez orada qo‘shiladi."

MAIN_KB = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🍽 Menyu", web_app=WebAppInfo(url=WEBAPP_URL))],
        ["📦 Buyurtmalarim"],
        ["📍 Manzilimiz", "☎️ Bog‘lanish"],
    ],
    resize_keyboard=True,
)


def som(n: int) -> str:
    return f"{n:,}".replace(",", " ") + " so‘m"


def load_menu() -> dict:
    """docs/menu.json dan menyuni o'qiydi: {id: {name, price, emoji, ...}}."""
    try:
        items = json.loads(MENU_FILE.read_text(encoding="utf-8"))
        return {str(i["id"]): i for i in items}
    except Exception as e:
        print("menu.json o‘qilmadi:", e)
        return {}


def load_orders() -> list:
    if ORDERS_FILE.exists():
        try:
            return json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_orders(orders: list) -> None:
    ORDERS_FILE.write_text(
        json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_admin_id():
    if ADMIN_FILE.exists():
        try:
            return int(ADMIN_FILE.read_text().strip())
        except ValueError:
            return None
    return None


def parse_order(raw: str, menu: dict):
    """Mini App yuborgan buyurtmani tekshiradi. Narxlarni menyudan o'zimiz olamiz."""
    try:
        data = json.loads(raw)
        items = {}
        for it in data.get("items", []):
            iid = str(it.get("id"))
            qty = int(it.get("qty", 0))
            if iid in menu and 1 <= qty <= 50:
                items[iid] = min(items.get(iid, 0) + qty, 50)
        address = str(data.get("address", "")).strip()[:300]
        phone = str(data.get("phone", "")).strip()[:30]
        payment = "💵 Naqd" if data.get("payment") == "naqd" else "💳 Karta"
    except Exception:
        return None
    if not items or len(address) < 3 or sum(c.isdigit() for c in phone) < 9:
        return None
    return {"items": items, "address": address, "phone": phone, "payment": payment}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Xush kelibsiz!\n\n"
        "🏠 Xayitboy ota CHOYXONA\n"
        "🍽 Ovqat buyurtma qilish botiga xush kelibsiz!\n\n"
        "Buyurtma berish uchun pastdagi «🍽 Menyu» tugmasini bosing.",
        reply_markup=MAIN_KB,
    )


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Sizning ID raqamingiz: {update.effective_user.id}")


async def web_app_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    menu = load_menu()
    parsed = parse_order(msg.web_app_data.data, menu)
    if not parsed:
        await msg.reply_text(
            "❌ Buyurtmani qabul qilib bo‘lmadi. Iltimos, menyudan qaytadan urinib ko‘ring.",
            reply_markup=MAIN_KB,
        )
        return

    user = update.effective_user
    lines, total = [], 0
    for iid, qty in parsed["items"].items():
        m = menu[iid]
        price = int(m["price"])
        lines.append(f"{m.get('emoji', '')} {m['name']} × {qty} = {som(price * qty)}".strip())
        total += price * qty

    orders = load_orders()
    order = {
        "id": len(orders) + 1,
        "user_id": user.id,
        "name": user.full_name,
        "username": user.username,
        "time": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "items": lines,
        "total": total,
        "address": parsed["address"],
        "phone": parsed["phone"],
        "payment": parsed["payment"],
    }
    orders.append(order)
    save_orders(orders)

    text = (
        f"🆕 Yangi buyurtma №{order['id']}\n\n"
        + "\n".join(lines)
        + f"\n\nJami: {som(total)}\n"
        f"💰 To‘lov: {order['payment']}\n"
        f"📍 Manzil: {order['address']}\n"
        f"📱 Telefon: {order['phone']}\n"
        f"👤 Mijoz: {user.full_name}"
        + (f" (@{user.username})" if user.username else "")
    )
    admin_id = get_admin_id()
    if admin_id:
        try:
            await context.bot.send_message(admin_id, text)
        except Exception as e:
            print("Adminga yuborib bo‘lmadi:", e)
    else:
        print(text)

    await msg.reply_text(
        f"✅ Buyurtmangiz №{order['id']} qabul qilindi!\n"
        f"Jami: {som(total)}\nTez orada bog‘lanamiz.",
        reply_markup=MAIN_KB,
    )


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mine = [o for o in load_orders() if o["user_id"] == uid][-5:]
    if not mine:
        await update.message.reply_text("📦 Hali buyurtmangiz yo‘q.")
        return
    parts = []
    for o in mine:
        parts.append(
            f"№{o['id']} • {o['time']}\n"
            + "\n".join(o["items"])
            + f"\nJami: {som(o['total'])} • {o['payment']}"
        )
    await update.message.reply_text("📦 Oxirgi buyurtmalaringiz:\n\n" + "\n\n".join(parts))


async def show_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ADDRESS_TEXT)


async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(CONTACT_TEXT)


async def old_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Eski klaviaturadagi tugmalar bosilsa, yangisini ko'rsatadi."""
    await update.message.reply_text(
        "Menyu yangilandi. Pastdagi «🍽 Menyu» tugmasini bosing.", reply_markup=MAIN_KB
    )


async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Faqat admin: rasm tagiga taom id sini (osh, shorva, ...) yozib yuboradi."""
    if update.effective_user.id != get_admin_id():
        return
    menu = load_menu()
    key = (update.message.caption or "").strip().lower()
    if key not in menu:
        await update.message.reply_text(
            "Rasm tagiga taom nomini yozib yuboring: " + ", ".join(menu.keys())
        )
        return
    file = await update.message.photo[-1].get_file()
    await file.download_to_drive(PHOTO_DIR / f"{key}.jpg")
    await update.message.reply_text(
        f"✅ {menu[key]['name']} rasmi saqlandi.\n"
        "Menyuda ko‘rinishi uchun uni GitHub'ga yuklang (sh yangila.sh)."
    )


def main():
    if not TOKEN_FILE.exists():
        print("token.txt topilmadi. Avval tokenni token.txt fayliga yozing.")
        return
    token = TOKEN_FILE.read_text().strip()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_order))
    app.add_handler(MessageHandler(filters.PHOTO, save_photo))
    app.add_handler(MessageHandler(filters.Regex("Buyurtmalarim"), my_orders))
    app.add_handler(MessageHandler(filters.Regex("Manzilimiz"), show_address))
    app.add_handler(MessageHandler(filters.Regex("Bog"), show_contact))
    app.add_handler(MessageHandler(filters.Regex("Menyu|Savatcha"), old_buttons))

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
