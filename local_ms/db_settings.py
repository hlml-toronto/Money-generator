DB_PATH = 'database_yfinance.db'

# list of ticker strings corresponding to yahoo finance tickers (to generate database)
DB_TICKERS = ['MSFT', 'AAPL', 'HUT', 'HUT.TO', 'SPY', 'CADUSD=X', 'BTC-USD', 'ETH-USD', 'ETHX-U.TO']

DB_TZ = 'US/Eastern'

MAP_COLUMN_TO_LABEL = {
    'open': 'Price (open)',
    'high': 'Price (high)',
    'low': 'Price (low)',
    'close': 'Price (close)',
    'volume': 'Volume (units)',
}
