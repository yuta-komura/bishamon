import datetime

import matplotlib.pyplot as plt

from lib import math
from lib import pandas_option as pd_op
from lib import repository

database = "tradingbot"
pd_op.display_max_columns()
pd_op.display_round_down()

print("--------------------------------------------")
print(
    ["fr_min1",
     55,
     "to_min1",
     0,
     "entry_min1",
     1,
     "close_min1",
     25,
     "fr_min2",
     26,
     "to_min2",
     31,
     "entry_min2",
     32,
     "close_min2",
     55])

asset = 1000000

sql = """
        select
            *
        from
            bitflyer_btc_ohlc_1M
        where
            (
                minute(Date) = 55
            or  minute(Date) = 0
            or  minute(Date) = 1
            or  minute(Date) = 25
            or  minute(Date) = 26
            or  minute(Date) = 31
            or  minute(Date) = 32
            )
        order by
            Date
        """
hp = repository.read_sql(database=database, sql=sql)

buy_rsis = []
sell_rsis = []
profits = []
for i in range(len(hp)):
    to_data = hp.iloc[i]
    to_Date = to_data["Date"]

    invalid_trading = \
        to_Date.hour in [4] \
        or to_Date.minute != 0 \
        or i - 1 < 0 \
        or i + 6 > len(hp) - 1

    if invalid_trading:
        continue

    fr_data = hp.iloc[i - 1]
    fr_Date = fr_data["Date"]

    entry_data = hp.iloc[i + 1]
    entry_Date = entry_data["Date"]

    close_data = hp.iloc[i + 2]
    close_Date = close_data["Date"]

    fr_data2 = hp.iloc[i + 3]
    fr_Date2 = fr_data2["Date"]

    to_data2 = hp.iloc[i + 4]
    to_Date2 = to_data2["Date"]

    entry_data2 = hp.iloc[i + 5]
    entry_Date2 = entry_data2["Date"]

    close_data2 = hp.iloc[i + 6]
    close_Date2 = close_data2["Date"]

    add_fr_Date = fr_Date + datetime.timedelta(hours=1)
    if add_fr_Date.hour != to_Date.hour or to_Date.hour != close_Date2.hour \
            or fr_Date.minute != 55 or entry_Date.minute != 1 or close_Date2.minute != 55:
        continue

    fr_Close = fr_data["Close"]
    to_Close = to_data["Close"]

    roc = (to_Close - fr_Close) / fr_Close

    amount = asset / entry_data["Open"]

    if roc < 0:
        profit = (amount * close_data["Open"]) - asset
    else:
        profit = asset - (amount * close_data["Open"])

    profits.append(profit)
    asset += profit

    fr_Close = fr_data2["Close"]
    to_Close = to_data2["Close"]

    roc = (to_Close - fr_Close) / fr_Close

    amount = asset / entry_data2["Open"]

    if roc < 0:
        profit = (amount * close_data2["Open"]) - asset
    else:
        profit = asset - (amount * close_data2["Open"])

    profits.append(profit)
    asset += profit

wins = []
loses = []
for i in range(len(profits)):
    if profits[i] > 0:
        wins.append(profits[i])
    elif profits[i] < 0:
        loses.append(profits[i])

pf = None
if sum(loses) != 0:
    pf = abs(sum(wins) / sum(loses))
pc = None
if len(wins) + len(loses) != 0:
    pc = len(wins) / (len(wins) + len(loses))
ic = None
if pc:
    ic = (2 * pc) - 1

start_date = hp.iloc[0]["Date"]
finish_date = hp.iloc[len(hp) - 1]["Date"]

print(start_date, "〜", finish_date)
print("profit", int(sum(profits)))
if pf:
    print("pf", math.round_down(pf, -2))
if pc:
    print("wp", math.round_down(pc * 100, 0), "%")
if ic:
    print("ic", math.round_down(ic, -2))
print("trading cnt", len(profits))

ps = []
p = 0
for i in range(len(profits)):
    ps.append(p)
    p += profits[i]

fig = plt.figure(figsize=(48, 24), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(ps))), ps)
plt.show()
