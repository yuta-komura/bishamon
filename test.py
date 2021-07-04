from datetime import datetime
from decimal import Decimal
from pprint import pprint

import pandas as pd
import requests

from lib import repository
from lib.mysql import MySQL

url = "https://api.bybit.com/v2/public/trading-records?symbol=BTCUSD"
response = requests.get(url=url)
records = response.json()["result"]

dates = []
sides = []
prices = []
sizes = []
for record in records:
    date = pd.to_datetime(record["time"]).tz_convert('Asia/Tokyo')
    side = record["side"].upper()
    price = Decimal(str(record["price"]))
    size = Decimal(str(record["qty"]))
    dates.append(date)
    sides.append(side)
    prices.append(price)
    sizes.append(size)

executions = pd.DataFrame({"date": dates,
                           "side": sides,
                           "price": prices,
                           "size": sizes})
executions = executions.sort_values("date")
executions = executions.reset_index(drop=True)
print(executions)
print("-------------------------")

url = "https://api.bybit.com/v2/public/orderBook/L2?symbol=BTCUSD"
response = requests.get(url=url)
records = response.json()["result"]

buy_prices = []
buy_sizes = []
sell_prices = []
sell_sizes = []
for record in records:
    side = record["side"].upper()
    price = Decimal(str(record["price"]))
    size = record["size"]
    if side == "BUY":
        buy_prices.append(price)
        buy_sizes.append(size)
    else:
        sell_prices.append(price)
        sell_sizes.append(size)

board_sell = pd.DataFrame(
    {"price": sell_prices, "size": sell_sizes}) \
    .sort_values("price", ascending=False)
board_buy = pd.DataFrame(
    {"price": buy_prices, "size": buy_sizes}) \
    .sort_values("price", ascending=False)

print(board_sell)
print("-------------------------")
print(board_buy)

# # bybit = ccxt.bybit({"apiKey": "50mOY6I7XRkQth9dLv",
# #                     "secret": "6d30dJ80nVHA8FWtBqFJs2Ut8tZn6aQbByij"})
# # balance = bybit.exe()
# # # /public/linear/recent-trading-records
# # print(balance)
