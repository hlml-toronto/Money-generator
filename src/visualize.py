import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.db_class import FinanceDB
from src.db_default import DB_ASSUMED_TZ, DB_V1_PATH


def plot_timeseries(df, ticker, column='close', interval='minutes'):

    MAP_COLUMN_TO_LABEL = {
        'open': 'Price (open)',
        'high': 'Price (high)',
        'low': 'Price (low)',
        'close': 'Price (close)',
        'volume': 'Volume (units)',
    }

    title = '%s (%s) for interval: %s' % (ticker, column, interval)
    ylabel = MAP_COLUMN_TO_LABEL[column]

    plt.plot(np.arange(len(df)), df[column])
    plt.title(title); plt.ylabel(ylabel)
    plt.show()

    df[column].plot()
    plt.title(title); plt.ylabel(ylabel)
    plt.show()
    return


def plot_timeseries_fancy(df, ticker, style='yahoo', interval='minutes', vol=True, start=None, end=None):
    """ Uses mplfinance package to make OHLC candle plot with volume subplot

    ticker: is either a string (to a DB ticker) or a pandas DataFrame
        if string: try reading the default database for that ticker; this fetches a DataFrame
        if DataFrame: no need to load the database

    If vol: plot volume subplot below primary plot
    style options:
        'binance', 'blueskies', 'brasil', 'charles', 'checkers',
        'classic', 'default', 'mike', 'nightclouds', 'sas',
        'starsandstripes', 'yahoo']
    """
    # slicing df based on datetime intervals
    if start is not None:
        start = pd.to_datetime(start).tz_localize(DB_ASSUMED_TZ)
        assert start >= df.index.min()
        df = df.loc[df.index > start]
    if end is not None:
        end = pd.to_datetime(end).tz_localize(DB_ASSUMED_TZ)
        assert end <= df.index.max()
        df = df.loc[df.index < end]

    kwargs = {'type': 'candle',
              'style': style,
              'volume': vol,
              'title': '%s (interval: %s)' % (ticker, interval),
              'ylabel': 'Price ($)',
              'ylabel_lower': 'Volume',
              'tz_localize': True}
    if interval == 'days':
        kwargs['mav'] = (50, 200)
    if interval == 'minutes':
        kwargs['mav'] = (15, 60)
    mpf.plot(df, **kwargs)
    return


def postprocess_db_timedata_per_ticker(df):
    df.drop(columns=['adjusted_close', 'security_ticker'], inplace=True)
    df.set_index(pd.DatetimeIndex(df['date']), inplace=True)
    df.index = df.index.tz_localize(DB_ASSUMED_TZ)
    return df


if __name__ == '__main__':

    finance_db = FinanceDB(DB_V1_PATH)
    ticker = 'AAPL'  # e.g. 'AAPL', 'MSFT', 'CADUSD=X', 'BTC-USD'

    # plot daily data
    df = finance_db.get_daily_per_ticker(ticker)
    df = postprocess_db_timedata_per_ticker(df)
    plot_timeseries_fancy(df, ticker, interval='days', start='2020-09-01', end='2021-11-21')

    # plot minutely data data
    df = finance_db.get_minutely_per_ticker(ticker)
    df = postprocess_db_timedata_per_ticker(df)
    minutely_start = datetime.today() - timedelta(days=20)
    minutely_end = datetime.today() - timedelta(days=4)
    plot_timeseries_fancy(df, ticker, interval='minutes', start=minutely_start, end=minutely_end)
