db_dir = 'financial_db'

db_tables = [ '''security ( ticker TEXT PRIMARY KEY,
                            company INT,
                            exchange INT,
                            currency TEXT
                            )''',
              '''exchange ( acronym TEXT PRIMARY KEY,
                            name TEXT,
                            time_zone TEXT,
                            FOREIGN KEY (acronym) REFERENCES security(exchange)
                            )''',
              '''company ( name TEXT PRIMARY KEY,
                            sector TEXT,
                            industry TEXT,
                            country TEXT,
                            market TEXT,
                            employees INT,
                            website TEXT,
                            FOREIGN KEY (name) REFERENCES security(company)
                            )''', # not sure if market is correct here
              '''security_price ( security_ticker INT,
                                  date TEXT,
                                  open REAL,
                                  high REAL,
                                  low REAL,
                                  close REAL,
                                  volume INT,
                                  adj_close REAL,
                                  CONSTRAINT price_daily_ticker PRIMARY KEY (security_ticker,date),
                                  FOREIGN KEY (security_ticker) REFERENCES security(ticker)
                                  )''',
              '''security_price_intraday (  security_ticker INT,
                                            time TEXT,
                                            open REAL,
                                            high REAL,
                                            low REAL,
                                            close REAL,
                                            volume INT,
                                            adj_close REAL,
                                            CONSTRAINT price_time_ticker PRIMARY KEY (security_ticker,time),
                                            FOREIGN KEY (security_ticker) REFERENCES security(ticker)
                                            )''',
              '''stock_adjustment ( security_ticker INT,
                                    date TEXT,
                                    CONSTRAINT adj_time_ticker PRIMARY KEY (security_ticker,date),
                                    FOREIGN KEY (security_ticker) REFERENCES security(ticker)
                                    )''' # missing some info.
         ]

db_tickers = ['MSFT', 'AAPL', 'HUT', 'HUT.TO', 'SPY', 'CADUSD=X', 'BTC-USD', 'ETH-USD', 'ETHX-U.TO']
