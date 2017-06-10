import requests

def init(bot):
	bot.handlers["train/info"] = info

def info(bot, message):
	TRAIN_NOT_FOUND = bot.render_message("train-not-found")

	train_number = message.text.replace("/train", "")

	schedule = bot.user_get(message.u_id, "schedule")

	for train in schedule:
		if train["id"] == train_number: break
	else:
		bot.telegram.send_message(message.u_id, TRAIN_NOT_FOUND)	
		return

	url = "https://api.rasp.yandex.net/v1.0/thread/?apikey=%s&format=json&system=express&uid=%s"%(bot.API_KEY, train["uid"])
	res = requests.get(url).json()

	stops = []
	for stop in res["stops"]:
		stop = {
			"title": stop["station"]["title"],
			"arrival": None if stop["arrival"] is None else stop["arrival"].split()[-1][:-3],
			"departure": None if stop["departure"] is None else stop["departure"].split()[-1][:-3],
			"type": stop["station"]["type"]
		}
		stops.append(stop)

	INFO = bot.render_message("train-info", train = train)
	STOPS = bot.render_message("stops", stops = stops[::-1], not_stops = train["stops"])
	
	bot.telegram.send_message(message.u_id, STOPS, parse_mode = "Markdown")
	bot.telegram.send_message(message.u_id, INFO, parse_mode = "Markdown")
	
