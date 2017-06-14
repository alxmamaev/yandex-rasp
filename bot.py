import logging
import json
import random
import codecs
import os
import importlib
import re

import redis
import telebot
import jinja2


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level = logging.INFO)

class Bot:
    def __init__(self, bot_name="super-bot", debug=False):
        self.logger = logging.getLogger(bot_name)
        self.logger.info("Starting bot")

        self.handlers = {}
        self.debug = debug
        self.callback_handlers = {}

        self.logger.info("Load config")
        self.const = {}
        self.const.update(json.loads(codecs.open("config/init.json", "r", "utf-8").read()))
        self.const["messages"] = json.loads(codecs.open("config/messages.json", "r", "utf-8").read())
        self.const["keyboards"] = json.loads(codecs.open("config/keyboards.json", "r", "utf-8").read())
        self.const["stations"] = json.loads(codecs.open("config/stations.json", "r", "utf-8").read())
        self.API_KEY = os.environ["API_KEY"]

        self.logger.info("Connect to Telegram")
        self.telegram = telebot.TeleBot(os.environ["BOT_TOKEN"])
        self.telegram.set_update_listener(self.proсess_updates)

        self.logger.info("Connect to Redis")
        self.redis = redis.from_url(os.environ.get("REDIS_URL","redis://localhost:6379"))

        self.logger.info("Collect modules")
        self._collect_modules()

        self.logger.info("Ready")

    def _collect_modules(self):
        for module_name in os.listdir("modules"):
            if module_name.endswith(".py"):
                module = importlib.import_module("modules.%s" % module_name[:-3])
                module.init(self)

    def user_set(self, user_id, field, value):
        key = "%s:%s" % (user_id, field)
        value = json.dumps(value)

        self.redis.set(key, value)

        self.logger.info("user:%s set[%s]: %s" % (user_id, field, value))

    def user_get(self, user_id, field, default=None):
        key = "%s:%s" % (user_id, field)
        value = self.redis.get(key)

        if type(value) is bytes: value = value.decode('utf-8')
        if value is not None: value = json.loads(value)
        else: value = default

        self.logger.info("user:%s get[%s]: %s" % (user_id, field, value))

        return value 

    def user_delete(self, user_id, field):
        key = "%s:%s" % (user_id, field)
        value = self.redis.delete(key)

        self.logger.info("user:%s delete[%s]: %s" % (user_id, field, value))
        
        return value

    def set_next_handler(self, user_id, handler):
        self.user_set(user_id, "next_handler", handler)

    def call_handler(self, handler, message, forward_flag=True):
        self.logger.info("user:%s call_handler[%s]" % (message.u_id, handler))
        
        if forward_flag: message.forward = True
        self.handlers[handler](self, message)

    
    def proсess_updates(self, updates):
        if type(updates) is telebot.types.Update:
            if updates.message is not None: self._process_message(updates.message)
            if updates.callback_query is not None: self._process_callback(updates.callback_query)
            return

        for update in updates:
            if type(update) is telebot.types.Message: self._process_message(update)
            if type(update) is telebot.types.CallbackQuery: self._process_message(update)

    def _process_message(self, message):
        message.u_id = message.chat.id
        message.forward = False
        if message.text == self.const["menu-button"]:
            self.call_handler(self.const["default-handler"], message, forward_flag = True)
            return
        
        current_handler = self.user_get(message.u_id, "next_handler", default = self.const["default-handler"])
        self.set_next_handler(message.u_id, self.const["default-handler"])

        try:
            self.call_handler(current_handler, message, forward_flag = False)
        except Exception as ex:
            self.logger.error(ex)
            if self.debug: raise ex
            self.set_next_handler(message.u_id, self.const["default-handler"])
            self.call_handler(self.const["default-handler"], message, forward_flag = True)

    def _process_callback(self, query):
        query.u_id = query.message.chat.id
        query.message.u_id = query.u_id
        if query.data:
            callback = query.data.split("/")[0]
            try:
                self.logger.info("user:%s callback[%s]"%(query.u_id, query.u_id))
                self.callback_handlers[callback](self, query)
            except Exception as ex:
                self.logger.error(ex)
                if self.debug: raise ex
        else: self.logger.error("user:%s callback[None]"%(query.u_id))

    def render_message(self, key, **kwargs):
        messages = self.const["messages"][key]
        
        if type(messages) is list: message = random.choice(messages)
        else: message = messages

        message = jinja2.Template(message)

        return message.render(**kwargs)

    def get_keyboard(self, keyboard):
        if keyboard is None: 
            markup = telebot.types.ReplyKeyboardRemove()
        else:
            if type(keyboard) is str: keyboard =  self.const["keyboards"][keyboard]
            markup = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard = True)
            for row in keyboard:
                keyboard_row = []
                for col in row: keyboard_row.append(telebot.types.KeyboardButton(col[0]))
                markup.row(*keyboard_row)
        
        return markup

    def get_inline_keyboard(self, keyboard):
        if type(keyboard) is str: keyboard =  self.const["keyboards"][keyboard]
        markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        for row in keyboard:
            keyboard_row = []
            for col in row: keyboard_row.append(telebot.types.InlineKeyboardButton(col[0], callback_data = col[1]))
            markup.row(*keyboard_row)

        return markup

    def get_key(self, keyboard, message):
        if type(keyboard) is str: keyboard = self.const["keyboards"][keyboard]
        for row in keyboard:
            for col in row:
                if message == col[0]: return col[1]