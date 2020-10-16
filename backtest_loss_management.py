import datetime

import matplotlib.pyplot as plt

from lib import math, repository

database = "tradingbot"

asset = 1000000

sql = """
        select
            *
        from
            bitflyer_btc_ohlc_1M
        WHERE
            (
            minute(Date) between 0 and 1
            or  minute(Date) between 44 and 59
            )
        order by
            Date
        """
historical_Price = repository.read_sql(database=database, sql=sql)

profits = []
asset_flow = []
for i in range(len(historical_Price)):
    try:
        now_data = historical_Price.iloc[i]
        now_Date = now_data["Date"]
        now_Close = now_data["Close"]

        if now_Date.minute == 0 \
                and now_Date.hour not in [4, 5, 18]:

            if (i - 1) < 0:
                continue

            past_data = historical_Price.iloc[i - 5]
            past_Date = past_data["Date"]

            entry_data = historical_Price.iloc[i + 1]
            entry_Date = entry_data["Date"]

            close_data = historical_Price.iloc[i + 2]
            close_Date = close_data["Date"]

            tD = past_Date + datetime.timedelta(hours=1)
            if tD.hour != now_Date.hour or now_Date.hour != entry_Date.hour or entry_Date.hour != close_Date.hour \
                    or past_Date.minute != 55 or entry_Date.minute != 1 or close_Date.minute != 44:
                continue

            past_Close = past_data["Close"]

            roc = (now_Close - past_Close) / past_Close

            entry_Price = entry_data["Open"]
            close_Price = close_data["Open"]

            amount = asset / entry_Price

            if roc < 0:
                profit = (amount * close_Price) - asset
                if profit < 0:
                    for j in range(0, 60):
                        try:
                            rema_data = historical_Price.iloc[(i + 2) + j]
                            rema_Date = rema_data["Date"]

                            if now_Date.hour != rema_Date.hour:
                                rema_Price = historical_Price.iloc[(
                                    i + 2) + (j - 1)]["Close"]
                                profit = (amount * rema_Price) - asset
                                break

                            rema_Price = rema_data["High"]
                            profit = (amount * rema_Price) - asset
                            if profit >= 0:
                                profit = 0
                                break
                        except Exception:
                            pass
            else:
                profit = asset - (amount * close_Price)
                if profit < 0:
                    for j in range(0, 60):
                        try:
                            rema_data = historical_Price.iloc[(i + 2) + j]
                            rema_Date = rema_data["Date"]

                            if now_Date.hour != rema_Date.hour:
                                rema_Price = historical_Price.iloc[(
                                    i + 2) + (j - 1)]["Close"]
                                profit = asset - (amount * rema_Price)
                                break

                            rema_Price = rema_data["Low"]
                            profit = asset - (amount * rema_Price)
                            if profit >= 0:
                                profit = 0
                                break
                        except Exception:
                            pass

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
print(start_date, "〜", finish_date)
print("asset", math.round_down(asset, 0))
print("profit", int(sum(profits)))
if pf:
    print("pf", math.round_down(pf, -2))
if wp:
    print("wp", math.round_down(wp, 0), "%")
print("trade_cnt", len(profits))

fig = plt.figure(figsize=(48, 24), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
plt.show()