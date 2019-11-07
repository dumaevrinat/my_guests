class Guest:
    def __init__(self, face_encoding, last_seen=None, first_seen=None, first_seen_this_interaction=None,
                 seen_count=None, name=None, uid=None):
        self.uid = uid
        self.last_seen = last_seen
        self.first_seen = first_seen
        self.first_seen_this_interaction = first_seen_this_interaction
        self.seen_count = seen_count
        self.face_encoding = face_encoding
        self.name = name

    def __str__(self):
        return 'Guest - uid: {}, name: {}, last_seen: {}, first_seen: {}, {}, seen_count: {}'.format(
            self.uid,
            self.name,
            self.last_seen,
            self.first_seen,
            self.first_seen_this_interaction,
            self.seen_count
        )

