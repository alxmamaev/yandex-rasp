import requests

def init(bot):
	bot.handlers["station/start"] = start
	bot.handlers["station/get-station-name"] = get_station_name
	bot.handlers["station/select-station"] = select_station
	bot.handlers["station/search"] = search
	bot.callback_handlers["station-show-shedule"] = show_shedule

def start(bot, message):
	GET_STATION = bot.render_message("get-station")
	BACK_TO_MENU_KEYBOARD = bot.get_keyboard("back-to-menu")
	bot.telegram.send_message(message.u_id, GET_STATION, reply_markup = BACK_TO_MENU_KEYBOARD)

	bot.user_delete(message.u_id, "station:1")
	bot.user_delete(message.u_id, "station:2")

	bot.set_next_handler(message.u_id, "station/get-station-name")

def get_station_name(bot, message):
	SELECT_STATION = bot.render_message("select-station")
	STATION_NOT_FOUND = bot.render_message("station-not-found")

	if not message.forward: 
		stations = bot.get_station(message.text)
		bot.user_set(message.u_id, "stations", stations)

		if not stations:
			bot.telegram.send_message(message.u_id, STATION_NOT_FOUND)	
			return	

		stations_keyboard = [[(station["name"].lower()+" ("+station["railway"].lower()+")", station["express"])] for station in stations]
		bot.user_set(message.u_id, "stations_keyboard", stations_keyboard)
	else:
		stations_keyboard = bot.user_get(message.u_id, "stations_keyboard")
	
	keyboard = bot.get_keyboard(stations_keyboard)

	if len(stations) == 1:
		bot.call_handler("station/select-station", message)
	else: 
		bot.telegram.send_message(message.u_id, SELECT_STATION, reply_markup = keyboard)
		bot.set_next_handler(message.u_id, "station/select-station")

def select_station(bot, message):
	GET_SECOND_station = bot.render_message("get-second-station")
	BACK_TO_MENU_KEYBOARD = bot.get_keyboard("back-to-menu")

	stations_keyboard = bot.user_get(message.u_id, "stations_keyboard")
	stations = bot.user_get(message.u_id, "stations")

	if len(stations) == 1: station = stations[0]["express"]
	else: station = bot.get_key(stations_keyboard, message.text)

	if not station:
		bot.call_handler(message.u_id, "station/get-station-name", message)
		return

	
	bot.user_set(message.u_id, "station:station", station)
	bot.call_handler("station/search", message)



def search(bot, message):
	SCHEDULE_IS_EMPTY = bot.render_message("schedule-is-empty")
	READY = bot.render_message("ready")
	BACK_TO_MENU_KEYBOARD = bot.get_keyboard("back-to-menu")

	station = bot.user_get(message.u_id, "station:station")

	schedule = []
	page = 1
	next_page = True
	while next_page:
		print(page)
		url = "https://api.rasp.yandex.net/v1.0/schedule/?apikey=%s&format=json&system=express&station=%s&lang=ru&transport_types=suburban&page=%s"%(bot.API_KEY, station, page)
		res = requests.get(url).json()
		
		next_page = res["pagination"]["has_next"]
		
		
		for i in res["schedule"]:
			a = {
				"id": i["thread"]["number"].replace("/", ""),
				"number": i["thread"]["number"],
				"uid": i["thread"]["uid"],
				"title": i["thread"]["title"],
				
				"arrival": i["departure"][:-3][:-3],
				"departure": i["arrival"][:-3][:-3],
				
				"days": i["days"],
				"excepted_days": i["except_days"],
				"stops": i["stops"].replace("кроме:", "") if "кроме:" in i["stops"] else ""
				
				
				
			}
			schedule.append(a)
		page += 1

	bot.user_set(message.u_id, "station:schedule", schedule)
	bot.user_set(message.u_id, "station:schedule:page", 0)
	
	if len(schedule) > 6: 
		keyboard = bot.get_inline_keyboard("more")
	else:
		keyboard = None

	if schedule:
		bot.telegram.send_message(message.u_id, READY, reply_markup = BACK_TO_MENU_KEYBOARD)
		SCHEDULE = bot.render_message("schedule", schedule = schedule[0:5])
		bot.telegram.send_message(message.u_id, SCHEDULE, parse_mode = "Markdown", reply_markup = keyboard)
	else:
		bot.telegram.send_message(message.u_id, SCHEDULE_IS_EMPTY, reply_markup = BACK_TO_MENU_KEYBOARD)
		self.call_handler(self.const["default-handler"], message)


def show_shedule(bot, query):
	page = bot.user_get(query.u_id, "schedule:page")
	schedule = bot.user_get(query.u_id, "schedule")

	SCHEDULE = bot.render_message("schedule", schedule = schedule[0:5])
	bot.telegram.edit_message_text(chat_id = query.u_id, message_id = query.message.message_id, text = SCHEDULE, parse_mode = "Markdown")

	page+=1
	bot.user_set(query.u_id, "schedule:page", page)

	if page*5+5 <= len(schedule):
		keyboard = bot.get_inline_keyboard("more")
	else:
		keyboard = None

	SCHEDULE = bot.render_message("schedule", schedule = schedule[page*5:page*5+5])
	bot.telegram.send_message(query.u_id, SCHEDULE, parse_mode = "Markdown", reply_markup = keyboard)