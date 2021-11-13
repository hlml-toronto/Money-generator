import sqlite3

from db_settings import DB_PATH, DB_TABLE_PRIMARY


class dbCursor:
    """
    Sample usage:
        with dbCursor() as cursor:
            cursor.execute("SQL COMMAND")
    """
    def __init__(self):
        self.db_path = DB_PATH

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.commit()
        self.connection.close()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, traceback)
        return


class db:

    def __init__(self):
        self.db_path = DB_PATH
        self.context_manager = dbCursor

    def reset(self):
        with dbCursor() as cursor:
            cursor.execute("DROP TABLE yfinance")
        return

    def rebuild(self):
        with dbCursor() as cursor:
            # Remove primary table
            self.reset()
            # Initialize primary table
            cursor.execute("""CREATE TABLE yfinance (
                first_name TEXT,
                last_name TEXT,
                email TEXT
            )""")
            # Fill primary table
            self.add_row('John', 'Smith', 'js@js.com')
            self.add_row('Mary', 'Smith', 'ms@ms.com')
            self.add_row('Donald', 'Duck', 'duck@disney.com')
        return

    def show_all(self):
        with dbCursor() as cursor:
            cursor.execute("SELECT rowid, * FROM {}".format(DB_TABLE_PRIMARY))  # use table global
            fulltable = cursor.fetchall()                                       # gets whole table
            for elem in fulltable:
                print(elem)
        return

    def add_row(self, first_name, last_name, email):
        with dbCursor() as cursor:
            cursor.execute("INSERT INTO yfinance VALUES (?,?,?)",
                           (first_name, last_name, email))
        return

    def add_manyrows(self, rows):
        # TODO what type of asserts on the structure of rows?
        with dbCursor() as cursor:
            cursor.executemany("INSERT INTO yfinance VALUES (?,?,?)",
                               rows)
        return

    def remove_row(self, column_name, row_value_to_delete):
        """
        Args:
            - column_name         - e.g. 'rowid'
            - row_value_to_delete - e.g. '1'
        Note:
            - column name and row value need to be passed differently to execute
        """
        with dbCursor() as cursor:
            # Option 1 (pass strings)
            execute_str = "DELETE FROM yfinance WHERE %s = %s" % (column_name, row_value_to_delete)
            cursor.execute(execute_str)
            # Option 2 (pass strings)
            #cursor.execute("DELETE FROM yfinance WHERE (%s) = (?)" % column_name,
            #               row_value_to_delete)
        return


if __name__ == '__main__':
    DB = db()
    DB.rebuild()

    print('\nShow all:')
    DB.show_all()

    print('\nRemove rowid #2')
    DB.remove_row('rowid', '2')

    print('\nShow all:')
    DB.show_all()
