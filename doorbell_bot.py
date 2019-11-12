import io
import logging
from datetime import datetime

import cv2
import face_recognition
import telebot
from telebot import apihelper

import utils
from config import PROXY, TOKEN, DATABASE_NAME
from database import Database
from guest import Guest

apihelper.proxy = PROXY
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(TOKEN)

db = Database(DATABASE_NAME)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    owners = db.select_owners()
    if message.from_user.username in owners:
        bot.send_message(message.chat.id, 'Hello')
        db.insert_chat(message.chat.id, message.from_user.username)


@bot.message_handler(commands=['guests'])
def send_guest_list(message):
    chat_ids = db.select_chat_ids()

    if message.chat.id in chat_ids:
        guests = db.select_guests()

        if len(guests) == 0:
            bot.send_message(message.chat.id, 'Guest list is empty')
        else:
            text = '\n\n'.join(map(str, guests))
            bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(commands=['delete_guest'])
def delete_guest(message):
    chat_ids = db.select_chat_ids()

    if message.chat.id in chat_ids:
        uid_list = message.text.split()[1:]
        if len(uid_list) == 0:
            bot.send_message(message.chat.id, 'Ids are incorrectly specified.')
        else:
            for uid in uid_list:
                if db.delete_guest_by_id(uid) == 0:
                    bot.send_message(message.chat.id, 'Guest with id: {} does not exist in database.'.format(uid))
                else:
                    bot.send_message(message.chat.id, 'Guest deleted: {}'.format(uid))


@bot.message_handler(content_types=['photo'])
def add_guest(message):
    chat_ids = db.select_chat_ids()

    if message.chat.id in chat_ids:
        temp_date = datetime(1999, 1, 1)
        name = message.caption

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image_file = io.BytesIO(downloaded_file)
        image = face_recognition.load_image_file(image_file)

        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)

        guests = db.select_guests()

        for face_encoding in face_encodings:
            guest = utils.lookup_known_face(face_encoding, guests)

            if guest is None:
                new_guest = Guest(face_encoding, temp_date, temp_date, temp_date, 0, name=name)
                db.insert_guest(new_guest)
                bot.send_message(message.chat.id, 'New guest added: {}.'.format(name))
            else:
                bot.send_message(message.chat.id, 'Guest is already in database.')

        if len(face_encodings) == 0:
            bot.send_message(message.chat.id, 'No faces found.')


def send_messages_to_owners(text):
    chat_ids = db.select_chat_ids()
    for chat_id in chat_ids:
        bot.send_message(chat_id, text)


def send_photo_to_owners(photo, caption):
    cv2.imwrite('detected_faces/face.jpg', photo)
    chat_ids = db.select_chat_ids()
    for chat_id in chat_ids:
        bot.send_photo(chat_id, open('detected_faces/face.jpg', 'rb'), caption=caption, parse_mode='Markdown')
