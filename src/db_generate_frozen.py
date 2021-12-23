import os
import random
import time

from db_default import DB_DIR
from db_class import FinanceDB


def generate_frozen_db(ticker_list, db_filename='default_finance_generated_frozen.db', sleep=True):
    # file must not already exist
    db_path = DB_DIR + os.sep + db_filename
    assert not os.path.isfile(db_path)
    # generate and fill the db
    finance_db = FinanceDB(db_filename)
    for ticker in ticker_list:
        finance_db.add_ticker(ticker)
        if sleep:
            time.sleep(random.randrange(1, 15))  # sleep for random number of seconds
    # get checksum
    db_checksum = finance_db.dbfile_md5(db_path)
    print('Generated db path:', db_path)
    print('Generated db filename:', db_filename)
    print('Generated db checksum:', db_checksum)
    print('\nTo standardize this database, push it and add entry to DB_FROZEN_VARIANTS in db_default.py')
    print('Each entry needs a label (e.g. v1, but that is taken) which is the key to a dict, containing...')
    print('\ttickers')
    print('\tdb_filename')
    print('\tmd5sum')
    return db_path, db_checksum


if __name__ == '__main__':
    frozen_ticker_list = ['BTC-USD', 'ETH-USD', 'ETHX-U.TO', 'BTCX-U.TO', 'CADUSD=X',
                          'GLXY.TO', 'COIN', 'BKCH', 'HBLK.TO', 'HBGD.TO',
                          'RIGZ', 'MIGI', 'LUXFF', 'FRTTF', 'DGHI.V',
                          'BTBT', 'GREE', 'DMGGF', 'RIOT', 'MARA',
                          'CLSK', 'ARBK', 'INTV', 'BITF.V', 'BITF',
                          'HUT', 'HUT.TO', 'HIVE', 'NCTY', 'BTCM',
                          'SDIG', 'SLNH', 'XPDI']
    generate_frozen_db(frozen_ticker_list)
