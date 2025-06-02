from telegram import Update
from telegram.ext import CallbackContext
from services.scheduler_service import SchedulerService

scheduler_service = SchedulerService()

def start_flight_search(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Flight search initiated! You will receive updates every 90 minutes.")
    scheduler_service.start_flight_search()