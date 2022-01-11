import requests
import random
from db_default import DB_DIR
import os

# TSX
tsx = requests.get("https://tsx.com/json/company-directory/search/tsx/%5E*")
tsx_json = tsx.json()

# NASDAQ
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0", }
nyse = requests.get("https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=10000&exchange=nyse",
                    headers=headers)
nyse_json = nyse.json()


def return_formatted_list_nyse(some_json):
    output = []
    table_rows = some_json["data"]["table"]["rows"]
    for entry in table_rows:
        if '^' not in entry["symbol"] and len(entry["symbol"].strip()) == len(entry["symbol"]):
            output.append(entry["symbol"])
    return output


def return_formatted_list_tsx(some_json):
    output = []
    table_rows = some_json["results"]
    for entry in table_rows:
        if entry["symbol"].count('.') < 2:
            reformatted = entry["symbol"].replace('.', '-')
            output.append(reformatted + ".TO")
    return output


def make_ticker_file(list_of_lists, descriptor, total_length):
    output = []
    for lst in list_of_lists:
        random_indices = random.sample(range(0, len(lst) - 1), int(total_length / 2.0))
        random_tickers = [lst[i] for i in random_indices]
        output.extend(random_tickers)

    with open(DB_DIR + os.sep + "frozen_" + descriptor + "_tickers.txt", mode='w') as output_txt:
        for ticker in output:
            output_txt.write(ticker + "\n")


if __name__ == '__main__':
    exchange_ticker_list = [return_formatted_list_tsx(tsx_json), return_formatted_list_nyse(nyse_json)]
    make_ticker_file(exchange_ticker_list, "small", 32)
    make_ticker_file(exchange_ticker_list, "medium", 64)
    make_ticker_file(exchange_ticker_list, "large", 128)
