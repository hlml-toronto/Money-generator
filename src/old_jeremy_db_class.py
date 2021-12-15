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
        empty_key = 'NULL'
        with DBCursor( self.db ) as cursor:
            # ticker info
            ticker_attr = ( info.get('symbol',empty_key), info.get('longName',empty_key),
                            info.get('exchange',empty_key),
                            info.get('financialCurrency',empty_key) )
            cursor.execute('''INSERT OR REPLACE INTO security
                                    ( ticker, company, exchange, currency )
                                    VALUES (?,?,?,?)''', ticker_attr )

            # exchange info
            exchange_attr = ( info.get('exchange',empty_key), info.get('exchangeName',empty_key),
                                info.get('exchangeTimezoneShortName',empty_key) )
            cursor.execute('''INSERT OR REPLACE INTO exchange
                                    ( acronym, name, time_zone )
                                    VALUES (?,?,?)''', exchange_attr)

            # company info
            company_attr = ( info.get('longName',empty_key), info.get('sector',empty_key),
                            info.get('industry',empty_key), info.get('country',empty_key),
                            info.get('market',empty_key), info.get('fullTimeEmployees',empty_key),
                            info.get('website',empty_key) )
            cursor.execute('''INSERT OR REPLACE INTO company
                ( name, sector, industry, country, market, employees, website )
                VALUES (?,?,?,?,?,?,?)''', company_attr )

            # ADD TABLE ABOUT STOCK ADJUSTMENT

    def add_security_price_daily(self, ticker, start=None, end=None):

        self.add_security(ticker)

        if start is None:
            time_series = yf.download(ticker, period='max')#, threads=True) # ask CN why
        else:
            times_series = yf.download(ticker, start=start, end=end)#, threads=True) # ask CN why

        time_series.index = time_series.index.strftime("%Y-%m-%d")

        time_series_tuples = time_series.to_records(index=True)

        list_time_series = [(*tuple([ticker]),*record) for record in time_series_tuples]

        with DBCursor( self.db ) as cursor:
            cursor.executemany('''INSERT OR REPLACE INTO security_price VALUES
                                    (?,?,?,?,?,?,?,?)''', list_time_series)

        return 0

    def add_security_price_minutely(self, ticker, start=None, end=None):

        self.add_security(ticker)

        if start is None:
            time_series = yf.download(ticker, period='1mo')#, threads=True) # ask CN why
        else:
            times_series = yf.download(ticker, start=start, end=end, interval='1m')#, threads=True)

        time_series.index = time_series.index.strftime("%Y-%m-%d %H:%M:%S")

        time_series_tuples = time_series.to_records(index=True)

        list_time_series = [(*tuple([ticker]),*record) for record in time_series_tuples]

        with DBCursor( self.db ) as cursor:
            cursor.executemany('''INSERT OR REPLACE INTO security_price_intraday VALUES
                                    (?,?,?,?,?,?,?,?)''', list(time_series_tuples))

        return 0

    def execute(self, sql_command):
        with DBCursor( self.db ) as cursor:
            cursor.execute( sql_command )
        return 0
