import sqlite3


class DB:
    def __init__(self, db_name):
        # Verbindung zur Datenbank herstellen
        conn = sqlite3.connect(db_name)
