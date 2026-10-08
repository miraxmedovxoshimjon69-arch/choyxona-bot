from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🍽 Menyu", "🛒 Savatcha"],
        ["📦 Buyurtmalarim"],
        ["📍 Manzilimiz", "☎️ Bog‘lanish"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 Xush kelibsiz!\n\n"
        "🏠 Xayitboy ota CHOYXONA\n"
        "🍽 Ovqat buyurtma qilish botiga xush kelibsiz!\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=reply_markup
    )

def main():
    TOKEN = "BOT_TOKEN_BU_YERGA"

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
