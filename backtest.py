import datetime

import matplotlib.pyplot as plt

from lib import math, repository

asset = 1000000

database = "tradingbot"


sql = """
        select
            *
        from
            (
                select
                    FROM_UNIXTIME(Time) as Date,
                    Open,
                    Close
                from
                    bitflyer_btc_ohlc_1M
            ) as b
        WHERE
            (minute(Date)  = 55
        or  minute(Date) between 0 and 1
        or  minute(Date) = 29)
        and
            Date >= '2020-9-15 00:00:00'
        order by
            Date
    """
historical_Price = repository.read_sql(database=database, sql=sql)

has_buy = False
has_sell = False
downs = []
downs_list = []
profits = []
asset_flow = []
for i in range(len(historical_Price)):
    try:
        now_data = historical_Price.iloc[i]
        now_Date = now_data["Date"]
        now_Close = now_data["Close"]

        if now_Date.minute == 0:
            past_data = historical_Price.iloc[i - 1]
            past_Date = past_data["Date"]

            entry_data = historical_Price.iloc[i + 1]
            entry_Date = entry_data["Date"]

            close_data = historical_Price.iloc[i + 2]
            close_Date = close_data["Date"]

            tD = past_Date + datetime.timedelta(hours=1)
            if tD.hour != now_Date.hour or now_Date.hour != entry_Date.hour or entry_Date.hour != close_Date.hour \
                    or past_Date.minute != 55 or entry_Date.minute != 1 or close_Date.minute != 29:
                continue

            past_Close = past_data["Close"]

            roc = (now_Close - past_Close) / past_Close

            entry_Price = entry_data["Open"]
            close_Price = close_data["Open"]

            amount = asset / entry_Price

            if roc < 0:
                print(entry_Date, "BUY")
                profit = (amount * close_Price) - asset
            else:
                print(entry_Date, "SELL")
                profit = asset - (amount * close_Price)

            if profit <= 0:
                downs.append(profit)
            else:
                downs_list.append(sum(downs))
                downs = []

            profits.append(profit)
            asset += profit
            asset_flow.append(asset)
    except Exception:
        pass

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
wp = None
if len(wins) + len(loses) != 0:
    wp = len(wins) / (len(wins) + len(loses)) * 100

start_date = historical_Price.iloc[0]["Date"]
finish_date = historical_Price.iloc[len(historical_Price) - 1]["Date"]

horizontal_line = "-------------------------------------------------"
print(horizontal_line)
print("backtest result")
print(start_date, "〜", finish_date)
print("asset", math.round_down(asset, 0))
print("profit", int(sum(profits)))
if pf:
    print("pf", math.round_down(pf, -2))
if wp:
    print("wp", math.round_down(wp, 0), "%")
print("trade_cnt", len(profits))
if downs_list:
    print("draw_down", int(min(downs_list)))

fig = plt.figure(figsize=(48, 24), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
plt.show()


"""
strategy(title="Hourly Anomaly", overlay=true, initial_capital=10000,
         default_qty_type=strategy.percent_of_equity, default_qty_value=100)
entry_min = 0
duration = 28
min = minute(time)
roc = (close[0] - close[5]) / close[5]

if (min == entry_min)
    if roc < 0
        strategy.entry("long", strategy.long)
    else
        strategy.entry("short", strategy.short)

if (min == entry_min + duration)
    strategy.close("long")
    strategy.close("short")

"""
