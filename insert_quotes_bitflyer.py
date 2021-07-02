import datetime
import sys
from pprint import pprint

import pytz
import requests

from lib import repository


def str_to_datetime(str_date: str):
    date = datetime.datetime.strptime(str_date[:-2], "%Y-%m-%dT%H:%M:%S.%f")
    date = pytz.utc.localize(date).astimezone(pytz.utc)
    date = date.astimezone(pytz.timezone("Asia/Tokyo"))
    return date


database = "tradingbot"
symbol_type = "PERP"

insert_table = f"quotes_bitflyer_{symbol_type.lower()}"
symbol_id = f"BITFLYERLTNG_{symbol_type}_BTC_JPY"
url = f"https://rest.coinapi.io/v1/quotes/{symbol_id}/history"

sql = "select * from coinapi_key"
data = repository.read_sql(database=database, sql=sql)
if data.empty:
    raise Exception("coinapi key is empty")

keys = list(data.key)

before_time_start = None
while True:

    sql = f"select date from {insert_table} order by date desc limit 1"
    data = repository.read_sql(database=database, sql=sql)
    if data.empty:
        time_start = "2000-01-01T00:00:00"
    else:
        latest_date = data.iloc[0]["date"].tz_localize("Asia/Tokyo")
        latest_date = latest_date.astimezone(pytz.utc)
        time_start = latest_date + datetime.timedelta(minutes=1)
        time_start_split = str(time_start).split()
        time_start = time_start_split[0] + \
            "T" + time_start_split[1].split("+")[0].split(".")[0]

        if before_time_start == time_start:
            print("complete")
            sys.exit()
        else:
            print("data insert")

    params = {
        "time_start": time_start,
        "limit": 10000}

    headers = {"X-CoinAPI-Key": keys[0]}

    response = requests.get(url, headers=headers, params=params).json()

    if "error" in response:
        pprint(response)
        if len(keys) - 1 <= 0:
            print("complete")
            sys.exit()
        else:
            del keys[0]
            continue

    try:
        for data in response:
            date = str_to_datetime(data["time_exchange"])
            ask_price = int(data["ask_price"])
            ask_size = str(data["ask_size"])
            bid_price = int(data["bid_price"])
            bid_size = str(data["bid_size"])
            sql = f"insert into {insert_table} values('{date}',{ask_price},'{ask_size}',{bid_price},'{bid_size}')"
            repository.execute(database=database, sql=sql, log=False)

    except Exception as e:
        print(e)
        pprint(data)

    before_time_start = time_start
