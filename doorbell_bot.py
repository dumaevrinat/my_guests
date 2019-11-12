import io
import logging
from datetime import datetime
from sqlite3 import IntegrityError

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


@bot.message_handler(commands=['owners'])
def send_owner_list(message):
    chat_ids = db.select_owner_chat_ids()

    if message.chat.id in chat_ids:
        owners = db.select_owners()

        text = '\n'.join(owners)
        bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['add_owners'])
def add_owners(message):
    chat_ids = db.select_owner_chat_ids()

    if message.chat.id in chat_ids:
        username_list = message.text.split()[1:]
        if len(username_list) == 0:
            bot.send_message(message.chat.id, 'Usernames are incorrectly specified.')
        else:
            for username in username_list:
                try:
                    db.insert_owner(username)
                    bot.send_message(message.chat.id, 'Owner *{}* added'.format(username), parse_mode='Markdown')
                except IntegrityError:
                    bot.send_message(message.chat.id, 'Owner *{}* is already in database.'.format(username), parse_mode='Markdown')


@bot.message_handler(commands=['delete_owners'])
def delete_owners(message):
    chat_ids = db.select_owner_chat_ids()

    if message.chat.id in chat_ids:
        username_list = message.text.split()[1:]
        if len(username_list) == 0:
            bot.send_message(message.chat.id, 'Usernames are incorrectly specified.')
        else:
            for username in username_list:
                if db.delete_owner_by_username(username) == 0:
                    bot.send_message(message.chat.id, 'Owner *{}* does not exist in database.'.format(username), parse_mode='Markdown')
                else:
                    bot.send_message(message.chat.id, 'Owner *{}* deleted'.format(username), parse_mode='Markdown')


@bot.message_handler(commands=['guests'])
def send_guest_list(message):
    chat_ids = db.select_owner_chat_ids()

    if message.chat.id in chat_ids:
        guests = db.select_guests()

        if len(guests) == 0:
            bot.send_message(message.chat.id, 'Guest list is empty')
        else:
            text = '\n\n'.join(map(str, guests))
            bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(commands=['delete_guests'])
def delete_guests(message):
    chat_ids = db.select_owner_chat_ids()

    if message.chat.id in chat_ids:
        uid_list = message.text.split()[1:]
        if len(uid_list) == 0:
            bot.send_message(message.chat.id, 'Ids are incorrectly specified.')
        else:
            for uid in uid_list:
                if db.delete_guest_by_id(uid) == 0:
                    bot.send_message(message.chat.id, 'Guest with id *{}* does not exist in database.'.format(uid), parse_mode='Markdown')
                else:
                    bot.send_message(message.chat.id, 'Guest with id *{}* deleted'.format(uid), parse_mode='Markdown')


@bot.message_handler(content_types=['photo'])
def add_guest(message):
    chat_ids = db.select_owner_chat_ids()

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
                bot.send_message(message.chat.id, 'New guest *{}* added.'.format(name), parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, 'Guest *{}* is already in database.'.format(name), parse_mode='Markdown')

        if len(face_encodings) == 0:
            bot.send_message(message.chat.id, 'Faces not found.')


def send_photo_to_owners(photo, caption):
    cv2.imwrite('detected_faces/face.jpg', photo)
    chat_ids = db.select_owner_chat_ids()
    for chat_id in chat_ids:
        bot.send_photo(chat_id, open('detected_faces/face.jpg', 'rb'), caption=caption, parse_mode='Markdown')
