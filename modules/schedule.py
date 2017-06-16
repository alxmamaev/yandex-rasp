import requests
import random
import Stemmer
import dateparser
import datetime

stemmer = Stemmer.Stemmer('russian')

def init(bot):
	bot.handlers["schedule/start"] = start
	bot.handlers["schedule/get-station-name"] = get_station_name
	bot.handlers["schedule/get-station-from-menu"] = stations_from_menu
	bot.handlers["schedule/select-station"] = select_station
	bot.handlers["schedule/search"] = search
	bot.handlers["schedule/get-time"] = get_time
	bot.callback_handlers["schedule-show-shedule"] = show_shedule

def autocorrector(text):
        url = "http://speller.yandex.net/services/spellservice.json/checkText"
        res = requests.post(url, data = {"text":text}).json()
        result = ""
        for i, ch in enumerate(text):
            for gram in res:
                if i == gram["pos"]: 
                    if not gram["s"]: gram["s"].append("")
                    result += gram["s"][0]
                    break
                elif gram["pos"]+gram["len"]>i>gram["pos"]: break
            else:
                result += ch
        return result


def make_ngramms(text):
    gramms = text.split("-")
    result = [[g] for g in gramms]
    if len(gramms)>1:
        for i in range(len(gramms)-1):
            result.append(gramms[i:i+2])
    if len(gramms)>2:
        for i in range(len(gramms)-2):
            result.append(gramms[i:i+3])
 
    result.sort(key = lambda x: len(x), reverse = True)
    
    for i, gramm in enumerate(result):
        result[i] = "-".join(gramm)
        
    result.sort(key = lambda x: len(x), reverse = True)
    
    _result = result[:]
    result = []
    for r in _result:
        if len(r)>2: result.append(r)
            
    return result   

def start(bot, message):
	GET_FIRST_STATION = bot.render_message("get-first-station")
	BACK_TO_MENU_KEYBOARD = bot.get_keyboard("back-to-menu")
	bot.telegram.send_message(message.u_id, GET_FIRST_STATION, reply_markup = BACK_TO_MENU_KEYBOARD)

	bot.user_delete(message.u_id, "schedule:station:1")
	bot.user_delete(message.u_id, "schedule:station:2")

	bot.set_next_handler(message.u_id, "schedule/get-station-name")

def stations_from_menu(bot, message):
	SELECT_STATION = bot.render_message("select-station")
	UNCORRECT_QUERY = bot.render_message("uncorrect-query")


	station_name = autocorrector(message.text).lower()
	station_name = station_name.replace("-", " ")
	station_name = station_name.split()
	station_name = stemmer.stemWords(station_name)
	station_name = "-".join(station_name)

	query = make_ngramms(station_name)

	flag = False
	stations = {}

	result = {}
	for g in query:
	    for station in bot.const["stations"]:
	        if g not in result or not flag:
	            flag = False
	            if station[3].startswith(g):
	                stations[g] = stations.get(g, []) + [station]
	    flag = True

	for key1 in list(stations.keys()):
	    for key2 in list(stations.keys()):
	        if key1 != key2 and key2 in key1:
	            stations.pop(key2)

	_stations = stations
	stations = []

	for station in list(_stations.keys()):
		stations.append([station_name.find(station), _stations[station]])

	stations.sort()
	if len(stations) > 1:
		stations = stations[0:2]
	else:
		bot.telegram.send_message(message.u_id, UNCORRECT_QUERY, parse_mode = "Markdown")	
		return	


	for i, station in enumerate(stations):
		print("STATIONS")
		print(station)
		station[1].sort(key = lambda x: len(x[2]))
		stations[i] = station[1]
	
	station_1 = stations[0][0][1]
	station_2 = stations[1][0][1]

	bot.user_set(message.u_id, "schedule:station:1", station_1)
	bot.user_set(message.u_id, "schedule:station:2", station_2)

	cur_date = datetime.date.today().strftime("%Y-%m-%d")
	bot.user_set(message.u_id, "schedule:date", cur_date)

	bot.call_handler("schedule/search", message)

	

def get_station_name(bot, message):
	GET_FIRST_STATION = bot.render_message("get-first-station")
	GET_SECOND_STATION = bot.render_message("get-second-station")
	SELECT_STATION = bot.render_message("select-station")
	STATION_NOT_FOUND = bot.render_message("station-not-found")

	if not message.forward: 

		station_name = autocorrector(message.text).lower()
		station_name = station_name.replace("-", " ")
		station_name = station_name.split()
		station_name = stemmer.stemWords(station_name)
		station_name = "-".join(station_name)

		query = make_ngramms(station_name)

		flag = False
		stations = {}

		result = {}
		for g in query:
		    for station in bot.const["stations"]:
		        if g not in result or not flag:
		            flag = False
		            if station[3].startswith(g):
		                stations[g] = stations.get(g, []) + [station]
		    flag = True

		for key1 in list(stations.keys()):
		    for key2 in list(stations.keys()):
		        if key1 != key2 and key2 in key1:
		            stations.pop(key2)

		_stations = stations
		stations = []

		for station in list(_stations.keys()):
			stations.append([station_name.find(station), _stations[station]])

		stations.sort()
		if stations: stations = stations[0][1]

		stations = [dict(zip(("railway", "express", "name", "stem"), station)) for station in stations]

		bot.user_set(message.u_id, "stations", stations)

		if not stations:
			station_1 = bot.user_get(message.u_id, "schedule:station:1")
			station_2 = bot.user_get(message.u_id, "schedule:station:2")

			bot.telegram.send_message(message.u_id, STATION_NOT_FOUND)
			if not station_1: bot.telegram.send_message(message.u_id, GET_FIRST_STATION)
			else: bot.telegram.send_message(message.u_id, GET_SECOND_STATION)

			bot.set_next_handler(message.u_id, "schedule/get-station-name")
			return	


		stations_keyboard = [[(station["name"].lower()+" ("+station["railway"].lower()+")", station["express"])] for station in stations]
		bot.user_set(message.u_id, "stations_keyboard", stations_keyboard)
	else:
		stations_keyboard = bot.user_get(message.u_id, "stations_keyboard")
	
	keyboard = bot.get_keyboard(stations_keyboard)

	if len(stations_keyboard) == 1:
		bot.call_handler("schedule/select-station", message)
	else: 
		bot.telegram.send_message(message.u_id, SELECT_STATION, reply_markup = keyboard)
		bot.set_next_handler(message.u_id, "schedule/select-station")

def select_station(bot, message):
	GET_SECOND_station = bot.render_message("get-second-station")
	BACK_TO_MENU_KEYBOARD = bot.get_keyboard("back-to-menu")
	MENU_KEYBOARD = bot.get_keyboard("menu")
	GET_DATE = bot.render_message("get-date")
	SELECT_STATION = bot.render_message("select-station")
	
	stations_keyboard = bot.user_get(message.u_id, "stations_keyboard")
	stations = bot.user_get(message.u_id, "stations")

	if len(stations) == 1: station = stations[0]["express"]
	else: station = bot.get_key(stations_keyboard, message.text)

	if not station:
		keyboard = bot.get_keyboard(stations_keyboard)
		bot.telegram.send_message(message.u_id, SELECT_STATION, reply_markup = keyboard)
		bot.set_next_handler(message.u_id, "schedule/select-station")
		return

	first_station = bot.user_get(message.u_id, "schedule:station:1")

	if not first_station:
		bot.user_set(message.u_id, "schedule:station:1", station)
		bot.telegram.send_message(message.u_id, GET_SECOND_station, reply_markup = BACK_TO_MENU_KEYBOARD)
		bot.set_next_handler(message.u_id, "schedule/get-station-name")
	else:
		bot.user_set(message.u_id, "schedule:station:2", station)
		bot.telegram.send_message(message.u_id, GET_DATE, reply_markup = BACK_TO_MENU_KEYBOARD)
		bot.set_next_handler(message.u_id, "schedule/get-time")
		
		

def get_time(bot, message):
	UNCORRECT_DATE = bot.render_message("uncorrect-date")
	READY = bot.render_message("ready")
	MENU_KEYBOARD = bot.get_keyboard("menu")

	date = dateparser.parse(message.text)
	if date: 
		date = date.strftime("%Y-%m-%d")
		bot.user_set(message.u_id, "schedule:date", date)
		
		bot.telegram.send_message(message.u_id, READY, reply_markup = MENU_KEYBOARD)
		
		bot.call_handler("schedule/search", message)
		bot.set_next_handler(message.u_id, "main-menu")
	else:
		bot.telegram.send_message(message.u_id, UNCORRECT_DATE, parse_mode = "Markdown")
		bot.set_next_handler(message.u_id, "schedule/get-time")


def search(bot, message):
	SCHEDULE_IS_EMPTY = bot.render_message("schedule-is-empty")
	BACK_TO_MENU_KEYBOARD = bot.get_keyboard("back-to-menu")

	from_station = bot.user_get(message.u_id, "schedule:station:1")
	to_station = bot.user_get(message.u_id, "schedule:station:2")

	schedule = []
	page = 1
	next_page = True
	while next_page:
		cur_date = datetime.date.today().strftime("%Y-%m-%d")
		date = bot.user_get(message.u_id, "schedule:date", default = cur_date)

		url = "https://api.rasp.yandex.net/v1.0/search/?apikey=%s&format=json&system=express&from=%s&to=%s&lang=ru&transport_types=suburban&page=%s&date=%s"%(bot.API_KEY, from_station, to_station, page, date)
		res = requests.get(url).json()
		
		next_page = res["pagination"]["has_next"]
		
		
		for i in res["threads"]:
			a = {
				"id": str(random.randint(100000,999999)),
				"number": i["thread"]["number"],
				"uid": i["thread"]["uid"],
				"title": i["thread"]["title"],
				
				"arrival": i["departure"].split()[-1][:-3],
				"departure": i["arrival"].split()[-1][:-3],
				
				"days": i.get("days", "ежедневно"),
				"excepted_days": i.get("except_days", ""),
				"stops": i["stops"].replace("кроме:", "") if "кроме:" in i["stops"] else "",
			}
			schedule.append(a)
		page += 1

	if date != cur_date: schedule[0]["date"] = ".".join(date.split("-")[::-1])
	else: schedule[0]["date"] = None

	bot.user_set(message.u_id, "schedule", schedule)
	bot.user_set(message.u_id, "schedule:page", 0)
	
	if len(schedule) > 6: 
		keyboard = bot.get_inline_keyboard("more")
	else:
		keyboard = None

	if schedule:
		print("render schedule", schedule, schedule[0]["date"])
		SCHEDULE = bot.render_message("schedule", schedule = schedule[0:5], date = schedule[0]["date"])
		bot.telegram.send_message(message.u_id, SCHEDULE, parse_mode = "Markdown", reply_markup = keyboard)
	else:
		bot.telegram.send_message(message.u_id, SCHEDULE_IS_EMPTY, reply_markup = BACK_TO_MENU_KEYBOARD)
		bot.call_handler(bot.const["default-handler"], message)


def show_shedule(bot, query):
	page = bot.user_get(query.u_id, "schedule:page")
	schedule = bot.user_get(query.u_id, "schedule")

	SCHEDULE = bot.render_message("schedule", schedule = schedule[0:5], date = schedule[0]["date"])
	bot.telegram.edit_message_text(chat_id = query.u_id, message_id = query.message.message_id, text = SCHEDULE, parse_mode = "Markdown")

	page+=1
	bot.user_set(query.u_id, "schedule:page", page)

	if page*5+5 <= len(schedule):
		keyboard = bot.get_inline_keyboard("more")
	else:
		keyboard = None

	SCHEDULE = bot.render_message("schedule", schedule = schedule[page*5:page*5+5], date = schedule[0]["date"])
	bot.telegram.send_message(query.u_id, SCHEDULE, parse_mode = "Markdown", reply_markup = keyboard)
