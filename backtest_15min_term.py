import datetime

import matplotlib.pyplot as plt

from lib import math, repository

m_nums = [55, 0, 1, 15, 10, 15, 16, 30, 25, 30, 31, 45, 40, 45, 46]
v = str(m_nums).replace("[", "").replace("]", "")

database = "tradingbot"

asset = 1000000

sql = """
        select
            *
        from
            bitflyer_btc_ohlc_1M
        WHERE
            minute(Date) in ({v})
        order by
            Date
        """.format(v=v)
historical_Price = repository.read_sql(database=database, sql=sql)


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

            close_data = historical_Price.iloc[i + 3]
            close_Date = close_data["Date"]

            past_add_Date = past_Date + datetime.timedelta(hours=1)
            if past_add_Date.hour != now_Date.hour or now_Date.hour != entry_Date.hour or entry_Date.hour != close_Date.hour \
                    or past_Date.minute != 55 or entry_Date.minute != 1 or close_Date.minute != 15:
                continue
        elif now_Date.minute == 15:
            past_data = historical_Price.iloc[i - 1]
            past_Date = past_data["Date"]

            entry_data = historical_Price.iloc[i + 1]
            entry_Date = entry_data["Date"]

            close_data = historical_Price.iloc[i + 3]
            close_Date = close_data["Date"]

            if past_Date.hour != now_Date.hour or now_Date.hour != entry_Date.hour or entry_Date.hour != close_Date.hour \
                    or past_Date.minute != 10 or entry_Date.minute != 16 or close_Date.minute != 30:
                continue
        elif now_Date.minute == 30:
            past_data = historical_Price.iloc[i - 1]
            past_Date = past_data["Date"]

            entry_data = historical_Price.iloc[i + 1]
            entry_Date = entry_data["Date"]

            close_data = historical_Price.iloc[i + 3]
            close_Date = close_data["Date"]

            if past_Date.hour != now_Date.hour or now_Date.hour != entry_Date.hour or entry_Date.hour != close_Date.hour \
                    or past_Date.minute != 25 or entry_Date.minute != 31 or close_Date.minute != 45:
                continue
        elif now_Date.minute == 45:
            past_data = historical_Price.iloc[i - 1]
            past_Date = past_data["Date"]

            entry_data = historical_Price.iloc[i + 1]
            entry_Date = entry_data["Date"]

            close_data = historical_Price.iloc[i + 3]
            close_Date = close_data["Date"]

            close_sub_Date = close_Date - datetime.timedelta(hours=1)
            if past_Date.hour != now_Date.hour or now_Date.hour != entry_Date.hour or entry_Date.hour != close_sub_Date.hour \
                    or past_Date.minute != 40 or entry_Date.minute != 46 or close_Date.minute != 0:
                continue
        else:
            continue

        past_Close = past_data["Close"]

        roc = (now_Close - past_Close) / past_Close

        entry_Price = entry_data["Open"]
        close_Price = close_data["Open"]

        amount = asset / entry_Price

        if roc < 0:
            profit = (amount * close_Price) - asset
        else:
            profit = asset - (amount * close_Price)

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
pc = None
if len(wins) + len(loses) != 0:
    pc = len(wins) / (len(wins) + len(loses))
ic = None
if pc:
    ic = (2 * pc) - 1

start_date = historical_Price.iloc[0]["Date"]
finish_date = historical_Price.iloc[len(historical_Price) - 1]["Date"]

horizontal_line = "-------------------------------------------------"
print(horizontal_line)
print(start_date, "〜", finish_date)
print("profit", int(sum(profits)))
if pf:
    print("pf", math.round_down(pf, -2))
if pc:
    print("wp", math.round_down(pc * 100, 0), "%")
if ic:
    print("ic", math.round_down(ic, -2))
print("trading cnt", len(profits))

fig = plt.figure(figsize=(48, 24), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
plt.show()
