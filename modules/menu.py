def init(bot):
	bot.handlers["menu/start"] = start
	bot.handlers["main-menu"] = menu

def start(bot, message):
	START_MESSAGE = bot.render_message("start", username = message.from_user.username)
	MENU_KEYBOARD = bot.get_keyboard("menu")

	bot.telegram.send_message(message.u_id, START_MESSAGE, reply_markup = MENU_KEYBOARD, parse_mode="Markdown")

def menu(bot, message):
	MENU_KEYBOARD = bot.get_keyboard("menu")
	MENU_MESSAGE = bot.render_message("menu")

	key = bot.get_key("menu", message.text)

	if message.text == "/start": return bot.call_handler("menu/start", message)
	if key and not message.forward: return bot.call_handler(key, message, forward_flag=False)
	if message.text and message.text.startswith("/train"): return bot.call_handler("train/info", message, forward_flag=True)

	bot.user_delete(message.u_id, "schedule:station:1")
	bot.user_delete(message.u_id, "schedule:station:2")
	bot.user_delete(message.u_id, "stations_keyboard")

	if not message.forward: bot.call_handler("schedule/get-station-from-menu", message, forward_flag = False)
	else: 
		bot.set_next_handler(message.u_id, "main-menu")
		bot.telegram.send_message(message.u_id, MENU_MESSAGE, reply_markup = MENU_KEYBOARD)