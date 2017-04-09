def init(bot):
	bot.handlers["schedule/start"] = start
	bot.handlers["schedule/get-station-name"] = get_station_name
	bot.handlers["schedule/select-station"] = select_stantion
	bot.handlers["schedule/search"] = search
	bot.callback_handlers["show_shedule"] = 

def start(bot, message):
	GET_FIRST_STATION = bot.render_message("get-first-station")
	bot.telegram.send_message(message.u_id, GET_FIRST_STATION)

	bot.set_next_handler("schedule/get-station-name")

def get_station_name(bot, message):
	SELECT_STANTION = bot.render_message("station-not-found")
	STATION_NOT_FOUND = bot.render_message("station-not-found")

	if not message.forward: 
		stantions = bot.get_station(message.text)

		if not stantions:
			bot.telegram.send_message(message.u_id, STATION_NOT_FOUND)	
			return	

		stantions_keyboard = [(stantion["name"].lower()+" ("+stantion["railway"].lower()+")", stantion["express"]) for stantion in stantions]
		bot.user_set(message.u_id, "stantions_keyboard", stantions_keyboard)
	else:
		stantions_keyboard = bot.user_get(message.u_id, "stantions_keyboard")
	
	keyboard = bot.get_keyboard(stantions_keyboard)
	bot.telegram.send_message(message.u_id, SELECT_STANTION, reply_markup = keyboard)

	bot.set_next_handler(message.u_id, "schedule/select-station")


def select_stantion(bot, message):
	GET_SECOND_STANTION = bot.render_message("get-second-stantion")

	stantions_keyboard = bot.user_get(message.u_id, "stantions_keyboard")
	stantion = bot.get_key(stantions_keyboard, message.text)

	if not stantion:
		bot.call_handler(message.u_id, "schedule/get-station-name", message)
		return

	first_stantion = bot.user_get(message.u_id, "stantion:1")

	if not first_stantion:
		bot.user_set(message.u_id, "stantion:1", stantion)
		bot.telegram.send_message(message.u_id, GET_SECOND_STANTION)
	else:
		bot.user_set(message.u_id, "stantion:2", stantion)
		results = []

def search(bot, message):
	from_stantion = bot.user_get(message.u_id, "stantion:1")
	to_stantion = bot.user_get(message.u_id, "stantion:2")

	schedule = []
	page = 1
	next_page = True
	while next_page:
	    print(page)
	    url = "https://api.rasp.yandex.net/v1.0/search/?apikey=%s&format=json&system=express&from=%s&to=%s&lang=ru&transport_types=suburban&page=%s"%(bot.API_KEY, from_stantion, to_stantion, page)
	    res = requests.get(url).json()
	    
	    next_page = res["pagination"]["has_next"]
	    
	    
	    for i in res["threads"]:
	        a = {
	            "number": i["thread"]["number"],
	            "uid": i["thread"]["uid"],
	            "title": i["thread"]["title"],
	            
	            "arrival": i["arrival"],
	            "departure": i["departure"],
	            
	            "days": i["days"],
	            "excepted_days": i["except_days"],
	            
	            
	            
	        }
	        schedule.append(a)
	    page += 1

	bot.user_set(message.u_id, "schedule", schedule)
	bot.user_set(message.u_id, "schedule:page", 0)
	
	if len(schedule) > 5: 
		keyboard = bot.get_inline_keyboard([["Далее", "schedule/show-shedule"]])
	else:
		keyboard = None

	SCHEDULE = bot.render_message("shedule", schedule[0:5])
	bot.telegram.send_message(message.u_id, SCHEDULE, parse_mode = "Markdown", reply_markup = keyboard)


def show_shedule(bot, query):
	page = bot.user_get(message.u_id, "schedule:page")+1
	bot.user_set(message.u_id, "schedule:page", page)
	
	if page*5+5 >= len(schedule):
		keyboard = bot.get_inline_keyboard([["Далее", "schedule/show-shedule"]])
	else:
		keyboard = None

	SCHEDULE = bot.render_message("shedule", schedule[page*5:page*5+5])
	bot.telegram.send_message(message.u_id, SCHEDULE, parse_mode = "Markdown", reply_markup = keyboard)
