import yfinance as yf
import sqlite3
import datetime
import pandas as pd
import os
from pandas.tseries.offsets import BDay
from sqlite3 import Error
from src.db_default import DB_TABLES, DB_DIR, DB_TICKERS


class DBCursor:
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

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_filename)
        self.connection.execute("PRAGMA foreign_keys = 1")
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.commit()
        self.connection.close()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, traceback)
        return


class FinanceDB:
    """
    For now, this database creates tables and then lets people add to it depending on
    what stocks they're interested in. However, once we have a remote database, it will
    probably be necessary to have separate code that constructs/maintains database and
    code that interacts with it.

    Input
        db_filename (str) : file where database is/will be saved.
    """

    def __init__(self, db_filename):
        #self.db_dir = os.path.join(os.path.normpath(os.getcwd() + os.sep + os.pardir), DB_DIR)
        self.db_dir = DB_DIR
        self.db_path = os.path.join(self.db_dir, db_filename)
        if not os.path.isdir(self.db_dir):
            os.makedirs(self.db_dir)

        with DBCursor(self.db_path) as cursor:
            for tables in DB_TABLES:
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {tables}")

    def add_default_tickers(self):
        for symbol in DB_TICKERS:
            self.add_ticker(symbol)
        print("Finished adding default tickers.")

    def add_ticker(self, symbol):
        yf_ticker = yf.Ticker(symbol)
        ticker_info = yf_ticker.info

        with DBCursor(self.db_path) as cursor:

            # populate exchange table
            exchange_attributes = (ticker_info.get('exchange', "NULL"),
                                   ticker_info.get('exchangeTimezoneName', "NULL"),
                                   ticker_info.get('exchangeTimezoneShortName', "NULL"))
            cursor.execute("PRAGMA table_info(exchange)")
            wildcards = ','.join(['?'] * len(cursor.fetchall()))
            cursor.execute("INSERT OR IGNORE INTO exchange VALUES (%s)" % wildcards, exchange_attributes)

            # populate security table
            security_attributes = (symbol,
                                   ticker_info.get('shortName', "NULL"),
                                   ticker_info.get('longName', "NULL"),
                                   ticker_info.get('exchange', "NULL"),
                                   ticker_info.get('currency', "NULL"),
                                   ticker_info.get('quoteType', "NULL"),
                                   ticker_info.get('sector', "NULL"),
                                   ticker_info.get('industry', "NULL"),
                                   ticker_info.get('market', "NULL"),
                                   ticker_info.get('country', "NULL"),
                                   ticker_info.get('fullTimeEmployees', "NULL"),
                                   ticker_info.get('website', "NULL"))
            cursor.execute("PRAGMA table_info(security)")
            wildcards = ','.join(['?'] * len(cursor.fetchall()))
            cursor.execute("INSERT OR REPLACE INTO security VALUES (%s)" % wildcards, security_attributes)

            # populate price_daily table
            time_series_daily = yf.download(symbol, period='max', interval='1d', threads='true', progress=False)
            time_series_daily['security_ticker'] = [symbol] * len(time_series_daily.index)
            time_series_daily.index = time_series_daily.index.strftime("%Y-%m-%d %H:%M:%S")

            time_series_formatted = time_series_daily.itertuples()
            daily_data = tuple(time_series_formatted)

            cursor.execute("PRAGMA table_info(price_daily)")
            wildcards = ','.join(['?'] * len(cursor.fetchall()))
            cursor.executemany("INSERT OR IGNORE INTO price_daily VALUES (%s)" % wildcards, daily_data)

            # populate price_minutely table
            date_intervals = self.minutely_data_download_intervals()
            for date in date_intervals:
                time_series_minutely = yf.download(symbol, start=date[0], end=date[1], interval='1m',
                                                   threads='true', progress=False)
                time_series_minutely['security_ticker'] = [symbol] * len(time_series_minutely.index)
                time_series_minutely.index = time_series_minutely.index.strftime("%Y-%m-%d %H:%M:%S")

                time_series_formatted = time_series_minutely.itertuples()
                minutely_data = tuple(time_series_formatted)

                cursor.execute("PRAGMA table_info(price_minutely)")
                wildcards = ','.join(['?'] * len(cursor.fetchall()))
                cursor.executemany("INSERT OR IGNORE INTO price_minutely VALUES (%s)" % wildcards, minutely_data)

            # populate actions table
            actions = yf_ticker.actions
            actions['security_ticker'] = [symbol] * len(actions.index)
            actions.index = actions.index.strftime("%Y-%m-%d %H:%M:%S")

            actions_formatted = actions.itertuples()
            actions_data = tuple(actions_formatted)

            cursor.execute("PRAGMA table_info(actions)")
            wildcards = ','.join(['?'] * len(cursor.fetchall()))
            cursor.executemany("INSERT OR IGNORE INTO actions VALUES (%s)" % wildcards, actions_data)

        print(symbol, "add_ticker() data downloaded and populated in tables.")

    def minutely_data_download_intervals(self, optional_start=(datetime.datetime.today() - datetime.timedelta(29))):
        """Used to create date intervals when downloading any history (should be less than 30 days unsure...)
           in most efficient manner with interval less than 7d
        """
        intervals = []
        today = datetime.datetime.today()
        start = optional_start
        end = (start + datetime.timedelta(6))

        intervals.append([start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')])

        while end + datetime.timedelta(6) < today:
            start = (end + datetime.timedelta(1))
            end = (start + datetime.timedelta(6))

            intervals.append([start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')])

        if end + datetime.timedelta(1) < today:
            start = end + datetime.timedelta(1) - BDay(1)
            end = today - BDay(1)

            if start.strftime('%Y-%m-%d') != end.strftime('%Y-%m-%d'):
                intervals.append([start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')])

        return intervals

    def __drop_all_tables(self):

        with DBCursor(self.db_path) as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            for table in tables:
                cursor.execute("DROP TABLE %s" % table[0])

    def __create_table(self, create_table_sql):
        with DBCursor(self.db_path) as cursor:
            try:
                cursor.execute(create_table_sql)
            except Error as e:
                print(e)

    def dataframe_from_query(self, query):
        with DBCursor(self.db_path) as cursor:
            cursor.execute(query)
            output = cursor.fetchall()
            cols = list(map(lambda x: x[0], cursor.description))
            df = pd.DataFrame(output, columns=cols)
        return df

    def get_table(self, tablename):
        query = "SELECT * FROM %s" % tablename
        df = self.dataframe_from_query(query)
        return df

    def get_daily_per_ticker(self, ticker):
        query = "SELECT * FROM price_daily WHERE security_ticker='%s' ORDER BY date" % ticker
        df = self.dataframe_from_query(query)
        return df

    def get_minutely_per_ticker(self, ticker):
        query = "SELECT * FROM price_minutely WHERE security_ticker='%s' ORDER BY date" % ticker
        df = self.dataframe_from_query(query)
        return df

    def get_actions_per_ticker(self, ticker):
        query = "SELECT * FROM actions WHERE security_ticker='%s' ORDER BY date" % ticker
        df = self.dataframe_from_query(query)
        return df

    def get_present_tickers(self):
        with DBCursor(self.db_path) as cursor:
            query = "SELECT ticker FROM security"
            cursor.row_factory = lambda cursor, row: row[0]
            cursor.execute(query)
            output = cursor.fetchall()
        # TODO compare vs the below code
        #with DBcursor() as cursor:
        #    cursor.execute("SELECT ticker FROM security")
        #    output = [elem[0] for elem in cursor.fetchall()]
        return output

    def __TODO_actions_since_date(self, ticker, date):
        yf_ticker = yf.Ticker(ticker)
        actions = yf_ticker.actions
        actions['security_ticker'] = [ticker] * len(actions.index)
        actions.index = actions.index.strftime("%Y-%m-%d %H:%M:%S")
        actions_formatted = actions.itertuples()
        data = tuple(actions_formatted)

        cols = ["date", "dividends", "stock_splits", "security_ticker"]
        actions_df = pd.DataFrame(data, columns=cols)

        actions_since = actions_df[actions_df["date"] > date.strftime("%Y-%m-%d")]

        return actions_since

    def __TODO_fetch_minutely_starting_at(self, ticker, start):
        # must be run within 29 days to maintain continuity with existing dataset

        assert start > datetime.datetime.today() - datetime.timedelta(29)
        date_intervals = self.minutely_data_download_intervals(start)

        for date in date_intervals:
            time_series_minutely = yf.download(ticker, start=date[0], end=date[1], interval='1m', threads='true',
                                               progress=False)
            time_series_minutely['security_ticker'] = [ticker] * len(time_series_minutely.index)
            time_series_minutely.index = time_series_minutely.index.strftime("%Y-%m-%d %H:%M:%S")

            time_series_formatted = time_series_minutely.itertuples()
            data = tuple(time_series_formatted)

            return data

    def __TODO_fetch_daily_between(self, ticker, start, end):

        time_series_daily = yf.download(ticker, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'),
                                        interval='1d', threads='true', progress=False)
        time_series_daily['security_ticker'] = [ticker] * len(time_series_daily.index)
        time_series_daily.index = time_series_daily.index.strftime("%Y-%m-%d %H:%M:%S")

        time_series_formatted = time_series_daily.itertuples()
        data = tuple(time_series_formatted)

        return data

    def __TODO_update(self):
        """ Perform update of actions/daily-price/minutely-price and account for stock splits + dividends
            Work in progress
        """

        tickers_present = self.get_present_tickers()
        today = datetime.datetime.today()
        for ticker in tickers_present:

            latest_daily = datetime.datetime.strptime(self.get_daily_per_ticker(ticker)["date"].iloc[-1],
                                                      "%Y-%m-%d %H:%M:%S")
            latest_minutely = datetime.datetime.strptime(self.get_minutely_per_ticker(ticker)["date"].iloc[-1],
                                                         "%Y-%m-%d %H:%M:%S")

            actions_since = self.__TODO_actions_since_date(ticker, latest_daily)

            if actions_since.empty:

                if today > latest_daily + datetime.timedelta(1):

                    # do daily updates
                    daily_data = self.__TODO_fetch_daily_between(ticker, latest_daily, today)

                    with DBCursor(self.db_path) as cursor:
                        cursor.execute("PRAGMA table_info(price_daily)")
                        wildcards = ','.join(['?'] * len( cursor.fetchall() ))
                        cursor.executemany("INSERT OR IGNORE INTO price_daily VALUES (%s)" % wildcards, daily_data)

                    # do minutely updates
                    if today - datetime.timedelta(1) < latest_daily + datetime.timedelta(29):

                        minutely_data = self.__TODO_fetch_minutely_starting_at(ticker, today - datetime.timedelta(1))

                        with DBCursor(self.db_path) as cursor:
                            cursor.execute("PRAGMA table_info(price_minutely)")
                            wildcards = ','.join(['?'] * len( cursor.fetchall() ))
                            cursor.executemany("INSERT OR IGNORE INTO price_minutely VALUES (%s)" % wildcards,
                                               minutely_data)

                    else:
                        print("Updating this late (>29 days since last update) will break timeseries continuity.")

                else:
                    print(ticker, " data already up to date.")

            # TODO: else (create multiplication sequence to do serial dividend/split updates)
