import yfinance as yf
import sqlite3

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

if __name__ == "__main__":
	DB_TICKERS = ['MSFT', 'AAPL', 'HUT', 'HUT.TO', 'SPY', 'CADUSD=X', 'BTC-USD', 'ETH-USD', 'ETHX-U.TO']
	for ticker in DB_TICKERS:
		add_data(ticker, resolution='minute',mem=True)