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
                minute(Date) = 55
            or  minute(Date) between 0 and 1
            or  minute(Date) = 9
            )
        order by
            Date
        """
historical_Price = repository.read_sql(database=database, sql=sql)

profits = []
for i in range(len(historical_Price)):
    try:
        now_data = historical_Price.iloc[i]
        now_Date = now_data["Date"]
        now_Close = now_data["Close"]

        if now_Date.minute == 0 \
                and now_Date.hour not in [4, 5, 18]:

            if (i - 1) < 0:
                continue

            past_data = historical_Price.iloc[i - 1]
            past_Date = past_data["Date"]

            entry_data = historical_Price.iloc[i + 1]
            entry_Date = entry_data["Date"]

            close_data = historical_Price.iloc[i + 2]
            close_Date = close_data["Date"]

            tD = past_Date + datetime.timedelta(hours=1)
            if tD.hour != now_Date.hour or now_Date.hour != entry_Date.hour or entry_Date.hour != close_Date.hour \
                    or past_Date.minute != 55 or entry_Date.minute != 1 or close_Date.minute != 9:
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
    except Exception:
        pass

# if profits:  # ノイズ除外
    # c = sorted(profits, reverse=True)[int((len(profits) - 1) * 0.1)]
    # profits = [i for i in profits if i < c]
    # c = sorted(profits)[int((len(profits) - 1) * 0.1)]
    # profits = [i for i in profits if i > c]

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

ps = []
p = 0
for i in range(len(profits)):
    ps.append(p)
    p += profits[i]

fig = plt.figure(figsize=(48, 24), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(ps))), ps)
plt.show()
