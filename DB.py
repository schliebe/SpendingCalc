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

    def get_entry_sum(self, chat_id, tag=None, time_period=None):
        """Returns the sum of the selected values

        Computes the sum of all values if neither tag or time_period are
        specified.
        If the time period is specified only those results will be considered.
        If the tag is specified only these entries will be considered. If not
        the result of all tags will be computed.

        :param chat_id: Telegram chat_id of the user
        :param tag: Tag for the results
        :param time_period: Time period for the results
        """
        where = 'WHERE Tags.ChatID = ?'
        param = (chat_id,)
        if tag:
            where += ' AND Tags.Tag = ?'
            param = param + (tag,)
        if time_period:
            if time_period != 'all':
                # Entsprechende SQlite Modifikatioren einfügen
                # https://sqlite.org/lang_datefunc.html
                if time_period == '7day':
                    modifier = '-7 day'
                elif time_period == '30day':
                    modifier = '-30 day'
                elif time_period == 'month':
                    modifier = 'start of month'
                elif time_period == 'year':
                    modifier = 'start of year'

                where += ' AND date(Date) >= date("now", ?)'
                param = param + (modifier,)
        try:
            cursor = self.conn.cursor()
            command = '''
                SELECT Tags.Tag, SUM(Value)
                FROM Entry
                JOIN Tags
                ON Entry.Tag = T_ID
                {}
                GROUP BY Entry.Tag
                '''.format(where)
            cursor.execute(command, param)
            res = cursor.fetchall()
            return res
        except BaseException as e:
            raise e
