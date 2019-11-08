import face_recognition
import numpy as np


def lookup_known_face(face_encoding, guests):
    """
    Просмотреть есть ли лицо в guests
    """

    if len(guests) == 0:
        return None

    face_distances = face_recognition.face_distance(list(map(lambda g: g.face_encoding, guests)), face_encoding)
    best_match_index = np.argmin(face_distances)

    if face_distances[best_match_index] < 0.66:
        best_match_guest = guests[best_match_index]

        return best_match_guest

    return None
