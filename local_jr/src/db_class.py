import numpy, os
import sqlite3 as sql
import yfinance as yf
import pandas as pd

from src.db_default import db_tables, db_dir, db_tickers

class DBCursor():
    """
    This class saves having to write code to connect to the database and create
    a cursor every time. Instead, use

    with DBCursor(file) as cursor:
        cursor.execute()

    Once outside of the with statement it will commit and close the database
    automatically too.
    """
    def __init__(self, db_filename):
        self.db_filename = db_filename
        return None

    def __enter__(self):
        self.connection = sql.connect( self.db_filename )
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.commit()
        self.connection.close()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, traceback)
        return

class FinanceDB():
    """
    For now, this database creates tables and then lets people add to it depending on
    what stocks they're interested in. However, once we have a remote database, it will
    probably be necessary to have separate code that constructs/maintains database and
    code that interacts with it.

    Input
        db_filename (str) : file where database is/will be saved.
    """
    def __init__(self, db_filename):
        self.dir = os.path.join(os.getcwd(), db_dir)
        self.db = os.path.join(self.dir, db_filename)
        if not os.path.isdir( self.dir ):
            os.makedirs( self.dir )

        with DBCursor( self.db ) as cursor:
            for tables in db_tables:
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {tables}")

            for ticker in db_tickers:
                self.add_security(ticker)
                #add_security_price_daily(ticker)

    def add_security(self, ticker):
        if not isinstance(ticker, yf.ticker.Ticker): ticker = yf.Ticker(ticker)
        info = ticker.info
        # sometimes some attributes are missing... need to deal with this, for
        # now simply ignoring and resplacing
        missing = ['sector','industry','employees','website','fullTimeEmployees','exchangeName','longName']
        for key in missing:
            if key not in info.keys():
                info[key] = ''

        with DBCursor( self.db ) as cursor:
            # ticker info
            print(info['symbol'], info['longName'], info['exchange'], info['currency'])
            ticker_attr = ( info['symbol'], info['longName'], info['exchange'], info['currency'] )
            cursor.execute('''INSERT IGNORE INTO security ( ticker, company, exchange, currency ) VALUES (?,?,?,?)''',
                                    ticker_attr )

            # exchange info
            exchange_attr = ( info['exchange'], info['exchangeName'], info['exchangeTimezoneShortName'] )
            cursor.execute('''INSERT IGNORE INTO exchange ( acronym, name, time_zone ) VALUES (?,?,?)''',
                                    exchange_attr)

            # company info
            company_attr = ( info['longName'], info['sector'], info['industry'], info['country'], info['market'], info['fullTimeEmployees'], info['website'] )
            cursor.execute('''INSERT IGNORE INTO company ( name, sector, industry, country, market, employees, website ) VALUES (?,?,?,?,?,?,?)''',
                                    company_attr )

    def add_security_price_daily(self, ticker, start=None, end=None):

        self.add_security(ticker)

        if start is None:
            data = yf.download(ticker, period='max')
        else:
            data = yf.download(ticker, start=start, end=end)

        cursor.executemany('''INSERT IGNORE INTO security_price VALUES
                                (?,?,?,?,?,?,?,?)
                                ''',)

        #if ticker not in table: add it
        return 0

    def add_security_price_minutely(self, ticker):
         return 0

    def execute(self, sql_command):
        with DBCursor( self.db ) as cursor:
            cursor.execute( sql_command )
        return 0
