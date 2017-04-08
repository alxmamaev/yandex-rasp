def init(bot):
	bot.handlers["catalog/start"] = start 
	bot.handlers["catalog/get-drag"] = get_drag
	bot.handlers["catalog/get-place"] = get_place

def start(bot, message):
	GET_DRAG_NAME_MESSAGE = bot.render_message("get-drag")
	BACK_TO_MENU_KEYBOARD = bot.get_keyboard("back-to-menu")

	bot.telegram.send_message(message.u_id, GET_DRAG_NAME_MESSAGE, reply_markup = BACK_TO_MENU_KEYBOARD)
	bot.set_next_handler(message.u_id, "catalog/get-drag")

def get_drag(bot, message):
	GET_PLACE_MESSAGE = bot.render_message("get-place")
	COOL_MESSAGE = bot.render_message("cool")
	BACK_TO_MENU_KEYBOARD = bot.get_keyboard("back-to-menu")

	if not message.forward:
		bot.user_set(message.u_id, "сatalog:name", message.text)

	bot.telegram.send_message(message.u_id, COOL_MESSAGE)
	bot.telegram.send_message(message.u_id, GET_DRAG_NAME_MESSAGE, reply_markup = BACK_TO_MENU_KEYBOARD)
	bot.set_next_handler(message.u_id, "catalog/get-place")

def get_place(bot, message):
	OOPS_MESSAGE = bot.render_message("oops")

	if not message.location:
		bot.telegram.send_message(message.u_id, OOPS_MESSAGE)
		bot.call_handler("catalog/get-drag", message)
		return

	user_location = {"lat": message.location.latitude,
					"long": message.location.longitude}

	bot.user_set(message.u_id, "сatalog:place", user_location)
	