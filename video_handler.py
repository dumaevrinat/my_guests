from datetime import datetime, timedelta

import cv2
import face_recognition

from config import DATABASE_NAME
from database import Database
from doorbell_bot import send_messages_to_owners, send_photo_to_owners
from guest import Guest

import numpy as np


class VideoHandler:
    database = Database(DATABASE_NAME)

    def __init__(self, bot):
        self.bot = bot
        print(self.database.select_chat_ids())
        print(self.database.select_owners())

    def register_new_face(self, face_encoding):
        """
        Добавить лицо в guests
        """

        guest = Guest(face_encoding, datetime.now(), datetime.now(), datetime.now(), 1)
        self.database.insert_guest(guest)

    def lookup_known_face(self, face_encoding, frame):
        """
        Просмотреть есть ли лицо в guests
        """

        guests = self.database.select_guests()

        if len(guests) == 0:
            return None

        face_distances = face_recognition.face_distance(list(map(lambda g: g.face_encoding, guests)), face_encoding)
        best_match_index = np.argmin(face_distances)

        if face_distances[best_match_index] < 0.66:
            best_match_guest = guests[best_match_index]
            best_match_guest.last_seen = datetime.now()

            if datetime.now() - best_match_guest.first_seen_this_interaction > timedelta(minutes=5):
                best_match_guest.first_seen_this_interaction = datetime.now()
                best_match_guest.seen_count += 1
                print(best_match_guest)
                send_messages_to_owners(best_match_guest)
                send_photo_to_owners(frame)

            self.database.update_guest_by_id(best_match_guest)
            return best_match_guest
        return None

    def video_capture_loop(self):
        video_capture = cv2.VideoCapture(0)

        while True:
            ret, frame = video_capture.read()

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_location, face_encoding in zip(face_locations, face_encodings):
                temp_guest = self.lookup_known_face(face_encoding, frame)
                if temp_guest is None:
                    print('New visitor!')
                    send_messages_to_owners('New visitor')
                    send_photo_to_owners(frame)
                    self.register_new_face(face_encoding)

            cv2.imshow('Video', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()
