from threading import Thread

import telebot
from telebot import apihelper

from VideoHandler import VideoHandler
from config import PROXY, TOKEN
from database import Database


apihelper.proxy = PROXY
bot = telebot.TeleBot(TOKEN)

db = Database()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    owners = db.select_owners()
    if message.from_user.username in owners:
        bot.send_message(message.chat.id, 'Hello')
        db.insert_chat(message.chat.id, message.from_user.username)


@bot.message_handler(commands=['guests_list'])
def send_guest_list(message):
    chat_ids = db.select_chat_ids()
    if message.chat.id in chat_ids:
        guests = db.select_guests()
        for guest in guests:
            bot.send_message(message.chat.id, guest.name)


if __name__ == "__main__":

    video_handler = VideoHandler(bot)
    Thread(target=bot.polling).start()
    Thread(target=video_handler.video_capture_loop).start()
