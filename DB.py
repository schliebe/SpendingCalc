import sqlite3


class DB:
    def __init__(self, db_name):
        # Verbindung zur Datenbank herstellen
        self.conn = sqlite3.connect(db_name)
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
                        "Comment" TEXT,
                        PRIMARY KEY("E_ID" AUTOINCREMENT)
                    )
                    '''
                cursor.execute(command)
                print('New Database created!')
        except BaseException as e:
            raise e
