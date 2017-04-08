def init(bot):
	bot.handlers["menu/start"] = start
	bot.handlers["main-menu"] = menu

def start(bot, message):
	START_MESSAGE = bot.render_message("start", username = message.from_user.username)
	MENU_KEYBOARD = bot.get_keyboard("menu")

	bot.telegram.send_message(message.u_id, START_MES1SAGE, reply_markup = MENU_KEYBOARD)

def menu(bot, message):
	MENU_KEYBOARD = bot.get_keyboard("menu")
	MENU_MESSAGE = bot.render_message("menu")

	key = bot.get_key("menu", message.text)

	if message.text == "/start": return bot.call_handler("menu/start", message)
	if key and message.is_forward: return bot.call_handler(key, message.text, forward_flag=False)

	bot.telegram.send_message(message.u_id, MENU_MESSAGE, reply_markup = MENU_KEYBOARD)