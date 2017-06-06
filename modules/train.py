def init(bot):
	bot.handlers["train/info"] = info

def info(bot, message):
	TRAIN_NOT_FOUND = bot.render_message("train-not-found")

	train_number = message.text.replace("/train", "")

	page = bot.user_get(message.u_id, "schedule:page")
	schedule = bot.user_get(message.u_id, "schedule")

	for train in schedule:
		if train["id"] == train_number: break
	else:
		bot.telegram.send_message(message.u_id, TRAIN_NOT_FOUND)	
		return

	INFO = bot.render_message("train-info", train = train)
	bot.telegram.send_message(message.u_id, INFO, parse_mode = "Markdown")
