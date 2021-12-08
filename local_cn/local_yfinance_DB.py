import yfinance as yf
import sqlite3
import datetime
import pandas as pd
from sqlite3 import Error

DB_PATH = "chris_yfinance_testing.db"

class DBCursor:
    """
    Cursor context manager.
    Minimizes connection and cursor instance statements.

    """

    def __init__(self):
        self.db_path = DB_PATH

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute("PRAGMA foreign_keys = 1")
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.commit()
        self.connection.close()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, traceback)
        return

class SecuritiesDB:

    def __init__(self):
        self.db_file = DB_PATH

    def initialize_schema(self):

        security_table = """CREATE TABLE IF NOT EXISTS security (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            exchange TEXT,
            currency TEXT,
            type TEXT
            ) 
            """

        exchange_table = """CREATE TABLE IF NOT EXISTS exchange (
            exchange_name TEXT PRIMARY KEY,
            exchange_timezone TEXT,
            exchange_timezone_short TEXT
            )
            """

        company_table = """CREATE TABLE IF NOT EXISTS company (
            company_name TEXT,
            sector TEXT,
            hq_country TEXT,
            security_ticker TEXT,
            CONSTRAINT company_key PRIMARY KEY (security_ticker, company_name),
            FOREIGN KEY(security_ticker) REFERENCES security (ticker)
            )
            """

        price_per_day = """CREATE TABLE IF NOT EXISTS price_daily (
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adjusted_close REAL,
            volume INTEGER,
            security_ticker TEXT,
            CONSTRAINT price_day_key PRIMARY KEY (security_ticker, date),
            FOREIGN KEY(security_ticker) REFERENCES security (ticker)
            )
            """

        price_per_minute = """CREATE TABLE IF NOT EXISTS price_minutely (
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adjusted_close REAL,
            volume INTEGER,
            security_ticker TEXT,
            CONSTRAINT price_min_key PRIMARY KEY (security_ticker, date),
            FOREIGN KEY(security_ticker) REFERENCES security (ticker)
            )
            """

        actions_table = """CREATE TABLE IF NOT EXISTS actions (
            date TEXT,
            dividends REAL,
            stock_splits REAL,
            security_ticker TEXT,
            CONSTRAINT actions_key PRIMARY KEY (security_ticker, date),
            FOREIGN KEY(security_ticker) REFERENCES security (ticker)
            )
            """

        # make empty tables
        tables = [security_table, exchange_table, company_table,
                  price_per_day, price_per_minute, actions_table]

        for table in tables:
            self.__create_table(table)

    def start_end_max_week_intervals(self, optional_start=(datetime.datetime.today() - datetime.timedelta(29))):
        """Used to download any history (should be less than 30 days unsure...)
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
            start = end + datetime.timedelta(1)
            end = today
            intervals.append([start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')])

        return intervals

    def add_tickers(self, symbols):

        for symbol in symbols:
            yf_ticker = yf.Ticker(symbol)
            ticker_info = yf_ticker.info
            with DBCursor() as cursor:

                # populate security table
                security_attributes = (symbol,
                                       self.__pad_dict(ticker_info, 'longName'),
                                       self.__pad_dict(ticker_info, 'exchange'),
                                       self.__pad_dict(ticker_info, 'currency'),
                                       self.__pad_dict(ticker_info, 'quoteType'))

                cursor.execute("INSERT OR IGNORE INTO security VALUES (?,?,?,?,?)", security_attributes)

                # populate exchange table
                exchange_attributes = (self.__pad_dict(ticker_info, 'exchange'),
                                       self.__pad_dict(ticker_info, 'exchangeTimezoneName'),
                                       self.__pad_dict(ticker_info, 'exchangeTimezoneShortName'))

                cursor.execute("INSERT OR IGNORE INTO exchange VALUES (?,?,?)", exchange_attributes)

                # populate company table
                company_attributes = (self.__pad_dict(ticker_info, 'longName'),
                                      self.__pad_dict(ticker_info, 'sector'),
                                      self.__pad_dict(ticker_info, 'country'),
                                      symbol)

                cursor.execute("INSERT OR IGNORE INTO company VALUES (?,?,?,?)", company_attributes)

                # populate price_daily table

                time_series_daily = yf.download(symbol, period='max', interval='1d', threads='true', progress=False)
                time_series_daily['security_ticker'] = [symbol] * len(time_series_daily.index)
                time_series_daily.index = time_series_daily.index.strftime("%Y-%m-%d %H:%M:%S")

                time_series_formatted = time_series_daily.itertuples()
                data = tuple(time_series_formatted)

                wildcards = ','.join(['?'] * 8)

                cursor.executemany("INSERT OR IGNORE INTO price_daily VALUES (%s)" % wildcards, data)

                # populate price_minutely table

                date_intervals = self.start_end_max_week_intervals()

                for date in date_intervals:
                    time_series_minutely = yf.download(symbol, start=date[0], end=date[1], interval='1m',
                                                       threads='true', progress=False)
                    time_series_minutely['security_ticker'] = [symbol] * len(time_series_minutely.index)
                    time_series_minutely.index = time_series_minutely.index.strftime("%Y-%m-%d %H:%M:%S")

                    time_series_formatted = time_series_minutely.itertuples()
                    data = tuple(time_series_formatted)

                    wildcards = ','.join(['?'] * 8)

                    cursor.executemany("INSERT OR IGNORE INTO price_minutely VALUES (%s)" % wildcards, data)

                # populate actions table

                actions = yf_ticker.actions
                actions['security_ticker'] = [symbol] * len(actions.index)
                actions.index = actions.index.strftime("%Y-%m-%d %H:%M:%S")

                actions_formatted = actions.itertuples()
                data = tuple(actions_formatted)

                wildcards = ','.join(['?'] * 4)

                cursor.executemany("INSERT OR IGNORE INTO actions VALUES (%s)" % wildcards, data)
            print(symbol, " data downloaded and populated in tables. ")

    def fetch_minutely_starting_at(self, ticker, start):
        # must be run within 29 days to maintain continuity with existing dataset

        assert start > datetime.datetime.today() - datetime.timedelta(29)
        date_intervals = self.start_end_max_week_intervals(start)

        for date in date_intervals:
            time_series_minutely = yf.download(ticker, start=date[0], end=date[1], interval='1m', threads='true',
                                               progress=False)
            time_series_minutely['security_ticker'] = [ticker] * len(time_series_minutely.index)
            time_series_minutely.index = time_series_minutely.index.strftime("%Y-%m-%d %H:%M:%S")

            time_series_formatted = time_series_minutely.itertuples()
            data = tuple(time_series_formatted)

            return data

    def fetch_daily_between(self, ticker, start, end):

        time_series_daily = yf.download(ticker, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'),
                                        interval='1d', threads='true', progress=False)
        time_series_daily['security_ticker'] = [ticker] * len(time_series_daily.index)
        time_series_daily.index = time_series_daily.index.strftime("%Y-%m-%d %H:%M:%S")

        time_series_formatted = time_series_daily.itertuples()
        data = tuple(time_series_formatted)

        return data

    def get_table(self, tablename):

        with DBCursor() as cursor:
            cursor.execute("SELECT rowid,* FROM %s" % tablename)
            fulltable = cursor.fetchall()

        return fulltable

    def drop_all_tables(self):

        with DBCursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            for table in tables:
                cursor.execute("DROP TABLE %s" % table[0])

    def __create_table(self, create_table_sql):

        with DBCursor() as cursor:

            try:
                cursor.execute(create_table_sql)
            except Error as e:
                print(e)

    def __pad_dict(self, ticker_dict, key):

        if key not in ticker_dict.keys():
            return None
        else:
            return ticker_dict[key]

    def get_daily_per_ticker(self, ticker):

        with DBCursor() as cursor:
            query = "SELECT * FROM price_daily WHERE security_ticker=? ORDER BY date"
            cursor.execute(query, (ticker,))
            output = cursor.fetchall()
            cols = ["date", "open", "high", "low", "close", "adjusted_close", "volume", "security_ticker"]
            df = pd.DataFrame(output, columns=cols)

            return df

    def get_minutely_per_ticker(self, ticker):

        with DBCursor() as cursor:
            query = "SELECT * FROM price_minutely WHERE security_ticker=? ORDER BY date"
            cursor.execute(query, (ticker,))
            output = cursor.fetchall()
            cols = ["date", "open", "high", "low", "close", "adjusted_close", "volume", "security_ticker"]
            df = pd.DataFrame(output, columns=cols)

            return df

    def get_actions_per_ticker(self, ticker):

        with DBCursor() as cursor:
            query = "SELECT * FROM actions WHERE security_ticker=? ORDER BY date"
            cursor.execute(query, (ticker,))
            output = cursor.fetchall()
            cols = ["date", "dividends", "stock_splits", "security_ticker"]
            df = pd.DataFrame(output, columns=cols)

            return df

    def get_present_tickers(self):

        with DBCursor() as cursor:
            query = "SELECT ticker FROM security"
            cursor.row_factory = lambda cursor, row: row[0]
            cursor.execute(query)
            output = cursor.fetchall()
        return output

    def actions_since_date(self, ticker, date):

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

    def update(self):
        ''' Perform update of actions/daily-price/minutely-price and account for stock splits + dividends
            Work in progress
        '''

        tickers_present = self.get_present_tickers()
        today = datetime.datetime.today()
        for ticker in tickers_present:

            latest_daily = datetime.datetime.strptime(self.get_daily_per_ticker(ticker)["date"].iloc[-1],
                                                      "%Y-%m-%d %H:%M:%S")
            latest_minutely = datetime.datetime.strptime(self.get_minutely_per_ticker(ticker)["date"].iloc[-1],
                                                         "%Y-%m-%d %H:%M:%S")

            actions_since = self.actions_since_date(ticker, latest_daily)

            if actions_since.empty:

                if today > latest_daily + datetime.timedelta(1):

                    # do daily updates
                    daily_data = self.fetch_daily_between(ticker, latest_daily, today)

                    with DBCursor() as cursor:
                        wildcards = ','.join(['?'] * 8)
                        cursor.executemany("INSERT OR IGNORE INTO price_daily VALUES (%s)" % wildcards, daily_data)

                    # do minutely updates
                    if today - datetime.timedelta(1) < latest_daily + datetime.timedelta(29):

                        minutely_data = self.fetch_minutely_starting_at(ticker, today - datetime.timedelta(1))

                        with DBCursor() as cursor:
                            wildcards = ','.join(['?'] * 8)
                            cursor.executemany("INSERT OR IGNORE INTO price_minutely VALUES (%s)" % wildcards,
                                               minutely_data)

                    else:
                        print("Updating this late (>29 days since last update) will break timeseries continuity.")

                else:
                    print(ticker, " data already up to date.")

            # TODO: else (create multiplcation sequence to do serial dividend/split updates)

