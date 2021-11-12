import sqlite3

from db_settings import DB_PATH, DB_TABLE_PRIMARY


def db_show_all():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT rowid, * FROM {}".format(DB_TABLE_PRIMARY))  # note can use table global
    fulltable = cursor.fetchall()                                       # fetches whole table
    for elem in fulltable:
        print(elem)

    connection.commit()
    connection.close()
    return


def db_add_row(first_name, last_name, email):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("INSERT INTO yfinance VALUES (?,?,?)",
                   (first_name, last_name, email))

    connection.commit()
    connection.close()
    return


def db_add_manyrows(rows):
    # TODO what type of asserts on the structure of rows?

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.executemany("INSERT INTO yfinance VALUES (?,?,?)",
                       rows)

    connection.commit()
    connection.close()
    return


def db_remove_row(column_name, row_value_to_delete):
    """
    Args:
        - column_name         - e.g. 'rowid'
        - row_value_to_delete - e.g. '1'
    Note:
        - column name and row value need to be passed differently to execute
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Option 1 (pass strings)
    execute_str = "DELETE FROM yfinance WHERE %s = %s" % (column_name, row_value_to_delete)
    cursor.execute(execute_str)

    # Option 2 (pass strings)
    #cursor.execute("DELETE FROM yfinance WHERE (%s) = (?)" % column_name,
    #               row_value_to_delete)

    connection.commit()
    connection.close()
    return


def db_reset():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("DROP TABLE yfinance")

    connection.commit()
    connection.close()
    return


def db_rebuild():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Remove primary table
    db_reset()

    # Initialize primary table
    cursor.execute("""CREATE TABLE yfinance (
            first_name TEXT,
            last_name TEXT,
            email TEXT
        )""")

    # Fill primary table
    db_add_row('John', 'Smith', 'js@js.com')
    db_add_row('Mary', 'Smith', 'ms@ms.com')
    db_add_row('Donald', 'Duck', 'duck@disney.com')

    connection.commit()
    connection.close()
    return


if __name__ == '__main__':
    db_rebuild()

    print('\nShow all:')
    db_show_all()

    print('\nRemove rowid #2')
    db_remove_row('rowid', '2')

    print('\nShow all:')
    db_show_all()
