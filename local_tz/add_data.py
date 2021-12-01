import yfinance as yf
import sqlite3

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
        self.connection = sqlite3.connect( self.db_filename )
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.commit()
        self.connection.close()
        # if exc_type is not None:
        #     traceback.print_exception(exc_type, exc_value, traceback)
        return

def add_data(tickername, resolution='day', mem=False):

	ticker = yf.Ticker(tickername)

	if resolution == 'day':
		hist = ticker.history(period="max")

		## add some additional columns to the default dataframe and rearrange
		hist['Ticker'] = tickername
		hist['Year'] = hist.index.year
		hist['Month'] = hist.index.month
		hist['Day'] = hist.index.day
		hist = hist[['Year', 'Month', 'Day','Ticker', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']]

	elif resolution == 'minute':
		hist = ticker.history(period="7d", interval='1m')

		## add some additional columns to the default dataframe and rearrange
		hist['Ticker'] = tickername
		hist['Year'] = hist.index.year
		hist['Month'] = hist.index.month
		hist['Day'] = hist.index.day
		hist['Hour'] = hist.index.hour
		hist['Minute'] = hist.index.minute
		hist = hist[['Year', 'Month', 'Day', 'Hour', 'Minute','Ticker', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']]


	conn = sqlite3.connect('stocks.db')
	if resolution == 'day':
		table_name = 'daily_info'
		primary_index = 'Date'
	elif resolution == 'minute':
		table_name = 'minutely_info'
		primary_index = 'Datetime'

	hist.to_sql(table_name, conn, if_exists='append')

	## delete any duplicate rows
	c = conn.cursor()
	c.execute("""
		DELETE   FROM {0}
		where    rowid not in
         		(
         		SELECT  min(rowid)
         		FROM    {0}
         		GROUP BY
                 	{1}, Ticker
                 	)""".format(table_name, primary_index))
	conn.commit()
	conn.close()

	## optionally print out estimate of size of table, based on number of rows
	## columns: Date (TIMESTAMP), Year (Int), Month (Int), Day (Int), Ticker (TEXT), Open (Real),
	## 			High (Real), Low (Real), Close (Real), Volume (Int), Dividends (Int), Stock Splits (Int)
	if mem:
		conn = sqlite3.connect('stocks.db')
		c = conn.cursor()
		text_size = 8 # not sure of size of text fields
		c.execute("SELECT COUNT(*)  FROM {0}".format(table_name))
		items = c.fetchone()
		print("Table size: ", items[0]*1e-6*(text_size + 4 + 4 + 4 + text_size + 8 + 8 + 8 + 8 + 4 + 4 + 4), " MB")


def queryDatabase(tickername, from_time, to_time, resolution, value):

	assert value in ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']

	if resolution == 'day':
		table_name = 'daily_info'
		primary_index = 'Date'
	elif resolution == 'minute':
		table_name = 'minutely_info'
		primary_index = 'Datetime'

	with DBCursor('stocks.db') as cursor:
		cursor.execute("""SELECT {0} FROM {1}
							WHERE {2} > '{3}'
							AND {2} < '{4}'
							AND Ticker = '{5}'""".format(value, table_name, primary_index, from_time, to_time, tickername))

		output = cursor.fetchall()

	return output


if __name__ == "__main__":
	# DB_TICKERS = ['MSFT', 'AAPL', 'HUT', 'HUT.TO', 'SPY', 'CADUSD=X', 'BTC-USD', 'ETH-USD', 'ETHX-U.TO']
	# for ticker in DB_TICKERS:
	# 	add_data(ticker, resolution='day',mem=True)


	print(queryDatabase('MSFT', "2014-10-01", "2021-01-21", 'day', 'High'))
