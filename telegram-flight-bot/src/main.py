from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
from services.scheduler_service import SchedulerService

async def start_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Welcome! Press the button below to start the flight search.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Start Flight Search", callback_data='start_search')]])
    )

def main() -> None:
    app = ApplicationBuilder().token("6706834472:AAGyFqO3mHEaPBKRcFdA4p1yIvBXGmW6NBk").build()

    app.add_handler(CommandHandler("start", start_command))

    scheduler_service = SchedulerService()
    scheduler_service.start()

    app.run_polling()

if __name__ == "__main__":
    main()