db_dir = 'financial_db'

db_tables = ['''security (
                    ticker TEXT PRIMARY KEY,
                    name_short TEXT,
                    name_long TEXT,
                    exchange TEXT,
                    currency TEXT,
                    type TEXT,
                    sector TEXT,
                    industry TEXT,
                    market TEXT,
                    hq_country TEXT,
                    employees INT,
                    website TEXT,
                    FOREIGN KEY(exchange) REFERENCES exchange (exchange_name)
                    ) ''',
             '''exchange (
                    exchange_name TEXT PRIMARY KEY,
                    exchange_timezone TEXT,
                    exchange_timezone_short TEXT
                    )''',
             '''price_daily (
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
                    )''',
             '''price_minutely (
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
                    )''',
             '''actions (
                    date TEXT,
                    dividends REAL,
                    stock_splits REAL,
                    security_ticker TEXT,
                    CONSTRAINT actions_key PRIMARY KEY (security_ticker, date),
                    FOREIGN KEY(security_ticker) REFERENCES security (ticker)
                    )'''
             ]

db_tickers = ['MSFT', 'AAPL', 'HUT', 'HUT.TO', 'SPY', 'CADUSD=X', 'BTC-USD', 'ETH-USD', 'ETHX-U.TO']
