def start_command(update, context):
    welcome_message = "Welcome to the Flight Search Bot! Press the button below to start searching for flights every 90 minutes."
    button = [[InlineKeyboardButton("Start Flight Search", callback_data='start_search')]]
    reply_markup = InlineKeyboardMarkup(button)

    update.message.reply_text(welcome_message, reply_markup=reply_markup)