from threading import Thread

import face_recognition
import cv2
from datetime import datetime, timedelta
import numpy as np

from config import TOKEN
from config import PROXY
from database import Database
from guest import Guest

import telebot
from telebot import apihelper

db = Database()

# temp_date = datetime(1999, 1, 1)
#
# rinat_image = face_recognition.load_image_file("faces/rinat.jpg")
# rinat_face_encoding = face_recognition.face_encodings(rinat_image)[0]
# rinat = Guest(rinat_face_encoding, temp_date, temp_date, temp_date, 0, name='Rinat Dumaev')
#
# dana_image = face_recognition.load_image_file("faces/dana.jpg")
# dana_face_encoding = face_recognition.face_encodings(dana_image)[0]
# dana = Guest(dana_face_encoding, temp_date, temp_date, temp_date, 0, name='Dana Pechatnova')
#
# db.insert_guest(rinat)
# db.insert_guest(dana)
# print(db.select_guests())

apihelper.proxy = PROXY
bot = telebot.TeleBot(TOKEN)

users_dict = {}
owners = ['dumaev']


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Hello')
    users_dict[message.from_user.username] = message.chat.id


def send_messages_to_owners(text, bot):
    for owner in owners:
        if owner in users_dict:
            bot.send_message(users_dict[owner], text)


def register_new_face(face_encoding):
    """
    Добавить лицо в guests
    """
    guest = Guest(face_encoding, datetime.now(), datetime.now(), datetime.now(), 1)
    db.insert_guest(guest)


def lookup_known_face(face_encoding, bot):
    """
    Просмотреть есть ли лицо в guests
    """

    guests = db.select_guests()

    if len(guests) == 0:
        return None

    face_distances = face_recognition.face_distance(list(map(lambda g: g.face_encoding, guests)), face_encoding)
    best_match_index = np.argmin(face_distances)

    if face_distances[best_match_index] < 0.6:
        guests[best_match_index].last_seen = datetime.now()

        if datetime.now() - guests[best_match_index].first_seen_this_interaction > timedelta(minutes=5):
            guests[best_match_index].first_seen_this_interaction = datetime.now()
            guests[best_match_index].seen_count += 1
            print(guests[best_match_index])
            send_messages_to_owners(guests[best_match_index], bot)

        db.update_guest_by_id(guests[best_match_index])
        return guests[best_match_index]
    return None


def video_capture_loop(bot):
    video_capture = cv2.VideoCapture(0)

    while True:
        ret, frame = video_capture.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_location, face_encoding in zip(face_locations, face_encodings):
            temp_guest = lookup_known_face(face_encoding, bot)
            if temp_guest is None:
                print('New visitor!')
                send_messages_to_owners('New visitor', bot)
                # Add the new face to our known face data
                register_new_face(face_encoding)

        # Display the final frame of video with boxes drawn around each detected fames
        cv2.imshow('Video', frame)

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    Thread(target=bot.polling).start()
    Thread(target=video_capture_loop, args=(bot,)).start()
