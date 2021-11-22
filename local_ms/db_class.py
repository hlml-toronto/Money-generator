import sqlite3
import yfinance as yf
from datetime import datetime, timedelta

from db_settings import DB_PATH, DB_TICKERS

"""
Overview: Database structure

Table #1: tickers
symbol    | currency | quoteType       | market     | exchange | longName  
------------------------------------------------------------------------------
MSFT      | USD      | EQUITY          | us_market  | NMS      | Microsoft Corporation
...       | ...      | ...             | ...        | ...      | ...
SPY       | USD      | ETF             | us_market  | PCX      | Apple Inc.
CADUSD=X  | USD      | CURRENCY        | ccy_market | CCY      | CAD/USD
CAD=X     | CAD      | CURRENCY        | ccy_market | CCY      | USD/CAD
BTC-USD   | CAD      | CRYPTOCURRENCY  | ccc_market | CCC      | Bitcoin USD

For each ticker there are several associated tables:

    Table: SPY_days
    date | open | high | low | close | volume
    ------------------------------------------------------------------------------
    1993-01-29   25.735677   25.735677   25.607639   25.717386   1003200
    ...
    2021-11-16  467.149994  470.489990  467.070007  469.279999  48707600
    
    Table: SPY_minutes 
    date | open | high | low | close | volume
    ------------------------------------------------------------------------------
    2021-11-16 09:30:00-05:00 	467.149994 	467.420013 	467.079987 	467.089996 	894038
    ...
    2021-11-16 13:08:00-05:00 	470.132507 	470.209991 	470.130096 	470.142487 	26438
    
Notes: data from yfinance package - ticker.ATTRIBUTE (e.g. msft.info) 

Notes: ticker.info   - dict with ~40 to ~150 keys depending on quoteType
- ETFs don't have 'financialCurrency', 'country', 'sector', 'industry'
- ETFs can have 'holdings' (list) and 'sectorWeightings' (list), but EQUITY generally won't

Notes: ticker.actions
- dataframe with 3 columns: Date, Dividends, and Stock Splits 
- this data is also available from ticker.history(period='max', actions=True)

Notes: ticker.splits
- dataframe with 2 columns: Date, [no name]

Notes: ticker.dividends
- dataframe with 2 columns: Date, [no name]

Attributes to consider adding
- sustainability
- recommendations
- options and options_chain
- quarterly_* (balancesheet, cashflow, earnings, financials)
"""


class DBcursor:
    """
    Sample usage
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


class DB:

    def __init__(self):
        self.db_path = DB_PATH
        # TODO check that main tickers are in there... maybe update them

    def list_tables(self, verbose=True):
        """
        Returns (and optionally prints) the list of tables which makeup the database
        """
        with DBcursor() as cursor:
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables_raw = cursor.fetchall()
            tables = [elem[0] for elem in tables_raw]
        if verbose:
            print('List of tables in db:', self.dbpath)
            print(tables)
        return tables

    def reset(self):
        """
        Removes all tables from the database
        """
        with DBcursor() as cursor:
            # Get list of tables
            tables = self.list_tables(verbose=False)
            # Delete each table
            for elem in tables:
                print('Deleting table:', elem)
                cursor.execute("DROP TABLE '%s'" % elem)
        return

    def rebuild(self):
        """
        Resets then rebuilds the database from scratch
        """
        with DBcursor() as cursor:
            # Remove primary table
            self.reset()
            # Fill primary table and ticker-specific tables
            for ticker_str in DB_TICKERS:
                self.add_ticker(ticker_str)
        return

    def show_table(self, tablename='tickers'):
        with DBcursor() as cursor:
            cursor.execute("SELECT rowid, * FROM {}".format(tablename))
            fulltable = cursor.fetchall()
            for elem in fulltable:
                print(elem)
        return

    def get_tickers(self, verbose=True):
        """
        Returns list of ticker strings from tickers table (empty list if table DNE)
        """
        tickers_list = []
        tables_list = self.list_tables(verbose=False)
        if 'tickers' in tables_list:
            with DBcursor() as cursor:
                cursor.execute("SELECT symbol FROM tickers")
                tickers_list = cursor.fetchall()
        if verbose:
            print(tickers_list)
        return tickers_list

    def initialize_table_tickers(self):
        with DBcursor() as cursor:
            # Create core tickers table if it doesn't exist
            cursor.execute("""CREATE TABLE IF NOT EXISTS tickers (
                symbol TEXT,
                currency TEXT,
                quoteType TEXT,
                market TEXT,
                exchange TEXT, 
                longName TEXT                
            )""")
        return

    def add_ticker(self, ticker_str, verbose=True):
        """
        Note: when creating a table with name given by the string tablename,
          care is needed if the string tablename contains a period;
          for SQL, the period is special, it denotes CREATE TABLE databasename.tablename.
        Example: for ticker ABC.TO, the tablename ABC.TO_days will have a period in it
        Safe solution: wrap the string formatter in quotes i.e. '%s' or '{}'
        """
        if verbose:
            print('Adding ticker %s from yahoo finance' % ticker_str)
        ticker = yf.Ticker(ticker_str)
        if verbose:
            print('\tInitial download complete')
        assert ticker.info['symbol'] == ticker_str
        self.initialize_table_tickers()  # initialize table if it does not exist

        # generate row info for one ticker
        # - replace shortName with longName if it exists
        if 'longName' in ticker.info.keys():
            ticker_longname = ticker.info['longName']
        else:
            ticker_longname = ticker.info['shortName']
        ticker_row = [ticker.info['symbol'],
                      ticker.info['currency'],
                      ticker.info['quoteType'],
                      ticker.info['market'],
                      ticker.info['exchange'],
                      ticker_longname]

        with DBcursor() as cursor:
            # Make sure ticker_str not already in tickers table
            cursor.execute("SELECT symbol FROM tickers WHERE symbol=(?)",
                           (ticker_str,))
            assert cursor.fetchone() is None
            # Add row for ticker
            cursor.execute("INSERT INTO tickers VALUES (?,?,?,?,?,?)", (ticker_row))
            if verbose:
                print('\tTicker row added to tickers table')

            # Add ticker specific tables (e.g. MSFT_days, MSFT_minutes)
            for timescale in ['minutes', 'days']:

                tablename = '%s_%s' % (ticker_str, timescale)
                # Create table header
                cursor.execute("""CREATE TABLE '{}' (
                        date TEXT,
                        open REAL,
                        high REAL,
                        low REAL,
                        close REAL,
                        volume INTEGER
                    )""".format(tablename))

                if timescale == 'days':
                    hist = ticker.history(period='max', interval='1d', actions=False)
                    hist.reset_index(inplace=True)
                    hist['Date'] = hist['Date'].astype(str)

                    # Fill table using historical data
                    cursor.executemany("INSERT INTO '{}' values (?,?,?,?,?,?)".format(tablename),
                                       (hist.values.tolist())
                                       )

                else:
                    date_end = datetime.today()
                    for idx in range(4):
                        # TODO care for duplicate rows -- add interval, 1m, to start time?
                        date_start = date_end - timedelta(days=6)
                        # can get intraday data up to 30-60d back, but can only pull 7d per download
                        hist = ticker.history(interval='1m', actions=False,
                                              start=date_start, end=date_end)
                        date_end = date_start
                        hist.reset_index(inplace=True)
                        hist['Datetime'] = hist['Datetime'].astype(str)

                        # Fill table using historical data
                        cursor.executemany("INSERT INTO '{}' values (?,?,?,?,?,?)".format(tablename),
                                           (hist.values.tolist())
                                           )


                if verbose:
                    print('\tTicker-specific table %s created and filled' % tablename)
        return

    def remove_ticker(self, ticker_str):
        with DBcursor() as cursor:
            # Remove row from table: tickers
            execute_str = "DELETE FROM tickers WHERE symbol=(?)"
            cursor.execute(execute_str,
                           (ticker_str,))
            # Remove associated ticker tables
            drop_table_days = "DROP TABLE %s_days" % ticker_str
            drop_table_minutes = "DROP TABLE %s_minutes" % ticker_str
            cursor.execute(drop_table_days)
            cursor.execute(drop_table_minutes)
        return


if __name__ == '__main__':

    db = DB()
    db.rebuild()

    print('\nShow all:')
    db.show_table(tablename='tickers')
    print('List of tickers:')
    db.get_tickers(verbose=True)

    ticker_test = 'MSFT'
    print('\nRemoving a specific ticker:', ticker_test)
    db.remove_ticker(ticker_test)

    print('\nShow tickers:')
    db.show_table(tablename='tickers')
    print('List of tickers:')
    db.get_tickers(verbose=True)

    print('\nAdding back a specific ticker:', ticker_test)
    db.add_ticker(ticker_test)

    print('\nShow tickers:')
    db.show_table(tablename='tickers')
    print('List of tickers:')
    db.get_tickers(verbose=True)
