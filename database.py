import io
import sqlite3
from sqlite3 import Error

import numpy

from guest import Guest


def adapt_array(array):
    out = io.BytesIO()
    numpy.save(out, array)
    out.seek(0)

    return sqlite3.Binary(out.read())


def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return numpy.load(out)


def create_connection(db_file):
    sqlite3.register_adapter(numpy.ndarray, adapt_array)
    sqlite3.register_converter('array', convert_array)

    connect = None
    try:
        connect = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
        connect.row_factory = sqlite3.Row
    except Error as e:
        print(e)
    return connect


class Database:
    def __init__(self):
        self.name = 'my_guests.db'
        # self.connect = create_connection('my_guests.db')

        with create_connection(self.name) as connect:
            cursor = connect.cursor()
            cursor.execute('''
            create table if not exists guests (
                id integer primary key, 
                name text,
                last_seen timestamp,
                first_seen timestamp,
                first_seen_this_interaction timestamp,
                seen_count integer,
                face_encoding array )
            ''')

            cursor.execute('''
            create table if not exists owners (
                username text primary key)
            ''')

            cursor.execute('''
            create table if not exists user_chats (
                username text primary key,
                chat_id integer)
            ''')

            connect.commit()

    def insert_guest(self, guest):
        with create_connection(self.name) as connect:
            cursor = connect.cursor()
            cursor.execute(
                ''' insert into guests (name, last_seen, first_seen, first_seen_this_interaction, seen_count, face_encoding)
                values (?, ?, ?, ?, ?, ?)''',
                (guest.name,
                 guest.last_seen,
                 guest.first_seen,
                 guest.first_seen_this_interaction,
                 guest.seen_count,
                 guest.face_encoding)
            )
            connect.commit()

    def update_guest_by_id(self, guest):
        with create_connection(self.name) as connect:
            cursor = connect.cursor()
            cursor.execute(
                '''
                update guests set name=?, last_seen=?, first_seen=?, first_seen_this_interaction=?, seen_count=?, face_encoding=? 
                where id=?''',
                (guest.name,
                 guest.last_seen,
                 guest.first_seen,
                 guest.first_seen_this_interaction,
                 guest.seen_count,
                 guest.face_encoding,
                 guest.uid)
            )
            connect.commit()

    def select_guests(self):
        guest_list = []
        with create_connection(self.name) as connect:
            cursor = connect.cursor()
            rows = cursor.execute('select * from guests')
            for row in rows:
                guest = Guest(row['face_encoding'],
                              row['last_seen'],
                              row['first_seen'],
                              row['first_seen_this_interaction'],
                              row['seen_count'],
                              row['name'],
                              row['id'])
                guest_list.append(guest)

        return guest_list

    def insert_owner(self, username):
        with create_connection(self.name) as connect:
            cursor = connect.cursor()
            cursor.execute(
                'insert into owners (username) values (?)', (username,))
            connect.commit()

    def select_owners(self):
        owners = set()
        with create_connection(self.name) as connect:
            cursor = connect.cursor()
            rows = cursor.execute('select * from owners')
            for row in rows:
                owners.add(row['username'])

        return owners

    def insert_chat(self, chat_id, username):
        with create_connection(self.name) as connect:
            cursor = connect.cursor()
            cursor.execute(
                'insert into user_chats (username, chat_id) values (?, ?)', (username, chat_id))
            connect.commit()

    def select_chats(self):
        chats = {}
        with create_connection(self.name) as connect:
            cursor = connect.cursor()
            rows = cursor.execute('select * from user_chats')
            for row in rows:
                chats[row['username']] = row['chat_id']

        return chats

    def select_chat_ids(self):
        chat_ids = set()
        with create_connection(self.name) as connect:
            cursor = connect.cursor()
            rows = cursor.execute('select * from owners join user_chats on owners.username = user_chats.username')
            for row in rows:
                chat_ids.add(row['chat_id'])

        return chat_ids
