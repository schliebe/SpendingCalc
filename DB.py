import sqlite3


class DB:
    def __init__(self, db_name):
        # Verbindung zur Datenbank herstellen
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.check_new_db()

    def check_new_db(self):
        """Initializes the database if a new database has been created

        When trying to connect to the database it will be created if it didn't
        already exist. If there are no tables yet, we want to initialize the
        missing tables.
        """
        try:
            cursor = self.conn.cursor()
            # Überprüfen, ob Datenbank neu erstellt wurde
            command = '''
                SELECT name
                FROM sqlite_master
                WHERE type="table"
                '''
            cursor.execute(command)
            if len(cursor.fetchall()) == 0:
                # Tabellen in neuer Datenbank anlegen (sofern nötig)
                command = '''
                    CREATE TABLE "Tags" (
                        "T_ID" INTEGER NOT NULL,
                        "ChatID" INTEGER NOT NULL,
                        "Tag" TEXT NOT NULL,
                        "Position" INTEGER,
                        PRIMARY KEY("T_ID" AUTOINCREMENT)
                    )
                    '''
                cursor.execute(command)
                command = '''
                    CREATE TABLE "Entry" (
                        "E_ID" INTEGER NOT NULL,
                        "Tag" INTEGER,
                        "Value" REAL NOT NULL DEFAULT 0,
                        "Date" TEXT,
                        "Comment" TEXT,
                        PRIMARY KEY("E_ID" AUTOINCREMENT)
                    )
                    '''
                cursor.execute(command)
                print('New Database created!')
        except BaseException as e:
            raise e

    def get_tags(self, chat_id):
        """Return all the tags of a user

        :param chat_id: Telegram chat_id of the user
        :return: List of tags of the user
        """
        try:
            cursor = self.conn.cursor()
            command = '''
                SELECT Tag
                FROM Tags
                WHERE ChatID = ?
                '''
            cursor.execute(command, (chat_id,))
            fetch = cursor.fetchall()
            tags = []
            for tag in fetch:
                tags.append(tag[0])
            return tags
        except BaseException as e:
            raise e

    def add_tag(self, chat_id, tag):
        """Adds a tag to a user

        :param chat_id: Telegram chat_id of the user
        :param tag: Tag that should be added
        """
        try:
            cursor = self.conn.cursor()
            command = '''
                INSERT INTO Tags (ChatID, Tag)
                VALUES (?, ?)
                '''
            cursor.execute(command, (chat_id, tag,))
            self.conn.commit()
        except BaseException as e:
            raise e

    def add_entry(self, chat_id, tag, value, date, comment):
        """Adds a new entry

        :param chat_id: Telegram chat_id of the user
        :param value: Value for the entry
        :param tag: Tag for the entry
        :param date: Date for the entry
        :param comment: Comment for the entry
        """
        try:
            cursor = self.conn.cursor()
            command = '''
                SELECT T_ID
                FROM Tags
                WHERE ChatID = ? AND Tag = ?
                '''
            cursor.execute(command, (chat_id, tag,))
            tag_id = cursor.fetchone()[0]
            command = '''
                INSERT INTO Entry (Tag, Value, Date, Comment)
                VALUES (?, ?, ?, ?)
                '''
            cursor.execute(command, (tag_id, value, date, comment))
            self.conn.commit()
        except BaseException as e:
            raise e
