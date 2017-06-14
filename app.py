# -*- coding:utf-8 -*-?
import os
import flask
import telebot
import logging
from bot import Bot

WEBHOOK_URL = os.environ["WEBHOOK_URL"]+"/bot/"+os.environ["BOT_TOKEN"]
WEBHOOK_PATH = "/"+os.environ["BOT_TOKEN"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

app = flask.Flask(__name__)

@app.route("/bot/<token>", methods=['POST'])
def getMessage(token):
    if token == BOT_TOKEN:
        update = telebot.types.Update.de_json(flask.request.stream.read().decode("utf-8"))

        if update.message is not None: bot._process_message(update.message)
        if update.callback_query is not None: bot._process_callback(update.callback_query)
        return "", 200

@app.route("/")
def webhook():
    return "Hola!", 200

@app.route("/set")
def set_webhook():
    bot.telegram.remove_webhook()
    bot.telegram.set_webhook(url=WEBHOOK_URL)
    return "Webhook setted", 200
    
bot = Bot(debug=True)
if __name__=="__main__": app.run(port=8089)