import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.db_default import DB_ASSUMED_TZ, DB_FROZEN_VARIANTS
from src.db_class import FinanceDB


def plot_timeseries(df, ticker, column='close', interval='minutes'):

    MAP_COLUMN_TO_LABEL = {
        'open': 'Price (open)',
        'high': 'Price (high)',
        'low': 'Price (low)',
        'close': 'Price (close)',
        'volume': 'Volume (units)',
    }

    assert column in MAP_COLUMN_TO_LABEL.keys()
    ylabel = MAP_COLUMN_TO_LABEL[column]
    title = '%s (%s) for interval: %s' % (ticker, column, interval)

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

    Inputs:
    - start, end: assumed to be datetime.datetime objects
       e.g. start = datetime.today() - timedelta(days=20)
    """
    def validate_start_end_times(df, endpt, left_endpt=True):
        if endpt is not None:
            from pytz import timezone
            # enforce timezone of the specified start/end time
            if isinstance(endpt, pd._libs.tslibs.timestamps.Timestamp):
                assert endpt.tz.zone == DB_ASSUMED_TZ
            else:
                assert (isinstance(endpt, datetime) or isinstance(endpt, str))
                endpt = pd.to_datetime(endpt).tz_localize(DB_ASSUMED_TZ)
            # slice the dataframe
            if left_endpt:
                assert endpt >= df.index.min()
                df = df.loc[df.index > endpt]
            else:
                assert endpt <= df.index.max()
                df = df.loc[df.index < endpt]
        return df

    # slicing df based on datetime intervals
    # TODO because mpf is computing moving averages, maybe better to pass the whole df and use xlim
    df = validate_start_end_times(df, start, left_endpt=True)
    df = validate_start_end_times(df, end, left_endpt=False)

    kwargs = {'type': 'candle',
              'style': style,
              'volume': vol,
              'title': '%s (interval: %s)' % (ticker, interval),
              'ylabel': 'Price ($)',
              'ylabel_lower': 'Volume',
              'tz_localize': True,
              'warn_too_much_data': int(1e6)}
    if interval == 'days':
        kwargs['mav'] = (50, 200)
    if interval == 'minutes':
        kwargs['mav'] = (15, 60)
    mpf.plot(df, **kwargs)
    return


def postprocess_db_timedata_per_ticker(df):
    """ Intended use: immediate postprocessing on a database fetch
    E.g.
        df = finance_db.get_daily_per_ticker(ticker)
        df = postprocess_db_timedata_per_ticker(df)
    Notes:
    - Removes 'adjusted_close' and 'security_ticker'
    - The index of the returned dataframe will be <class 'pandas._libs.tslibs.timestamps.Timestamp'>
        - Note: that class inherits from datetime.datetime
    """
    df.drop(columns=['adjusted_close', 'security_ticker'], inplace=True)
    df.set_index(pd.DatetimeIndex(df['date']), inplace=True)
    df.index = df.index.tz_localize(DB_ASSUMED_TZ)
    return df


if __name__ == '__main__':

    # specify which database and instantiate the FinanceDB class
    db_variant_label = 'v1'
    db_filename = DB_FROZEN_VARIANTS['v1']['db_filename']
    finance_db = FinanceDB(db_filename)

    # choose a ticker from the database
    ticker = 'MSFT'  # e.g. 'AAPL', 'MSFT', 'CADUSD=X', 'BTC-USD'

    # plot daily data
    df = finance_db.get_daily_per_ticker(ticker)
    df = postprocess_db_timedata_per_ticker(df)
    plot_timeseries_fancy(df, ticker, interval='days', start='2020-01-01', end='2021-11-21')

    # plot minutely data data
    df = finance_db.get_minutely_per_ticker(ticker)
    df = postprocess_db_timedata_per_ticker(df)
    minutely_start = df.index.max() - timedelta(days=10)
    minutely_end = df.index.max() - timedelta(days=8)
    plot_timeseries_fancy(df, ticker, interval='minutes', start=minutely_start, end=minutely_end)
