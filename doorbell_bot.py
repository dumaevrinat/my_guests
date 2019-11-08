import cv2
import telebot
from telebot import apihelper

from config import PROXY, TOKEN, DATABASE_NAME
from database import Database

import numpy as np

apihelper.proxy = PROXY
bot = telebot.TeleBot(TOKEN)

db = Database(DATABASE_NAME)


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


# @bot.message_handler(content_types=['photo'])
# def add_guest(message):
#     file_id = message.photo[-1].file_id
#     file_info = bot.get_file(file_id)
#     downloaded_file = bot.download_file(file_info.file_path)
#     image = np.asarray(bytearray(downloaded_file), dtype="uint8")
#     image = cv2.imdecode(image, cv2.IMREAD_COLOR)
#


def send_messages_to_owners(text):
    chat_ids = db.select_chat_ids()
    for chat_id in chat_ids:
        bot.send_message(chat_id, text)


def send_photo_to_owners(photo):
    cv2.imwrite('detected_faces/face.jpg', photo)
    chat_ids = db.select_chat_ids()
    for chat_id in chat_ids:
        bot.send_photo(chat_id, open('detected_faces/face.jpg', 'rb'))
