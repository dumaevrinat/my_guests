from datetime import datetime, timedelta

import cv2
import face_recognition

import utils
from config import DATABASE_NAME
from database import Database
from doorbell_bot import send_photo_to_owners
from guest import Guest


class VideoHandler:
    database = Database(DATABASE_NAME)

    def __init__(self, bot):
        self.bot = bot
        print(self.database.select_owner_chat_ids())
        print(self.database.select_owners())

    def register_new_face(self, face_encoding):
        guest = Guest(face_encoding, datetime.now(), datetime.now(), datetime.now(), 1)
        self.database.insert_guest(guest)

    def video_capture_loop(self):
        video_capture = cv2.VideoCapture(0)

        while True:
            ret, frame = video_capture.read()

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            guests = self.database.select_guests()
            for face_encoding in face_encodings:
                guest = utils.lookup_known_face(face_encoding, guests)

                if guest is None:
                    print('New visitor!')
                    send_photo_to_owners(frame, 'New visitor!')
                    self.register_new_face(face_encoding)
                else:
                    guest.last_seen = datetime.now()

                    if datetime.now() - guest.first_seen_this_interaction > timedelta(minutes=5):
                        guest.first_seen_this_interaction = datetime.now()
                        guest.seen_count += 1
                        print(guest)
                        send_photo_to_owners(frame, str(guest))

                    self.database.update_guest_by_id(guest)

            cv2.imshow('Video', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()
