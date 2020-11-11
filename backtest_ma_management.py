import datetime

import matplotlib.pyplot as plt
import pandas as pd

from lib import math, repository

asset = 1000000

database = "tradingbot"
pd.set_option('display.max_columns', 100)

sql = """
        select
            *
        from
            bitflyer_btc_ohlc_1M
        order by
            Date
        """
mad = repository.read_sql(database=database, sql=sql)

mad["9ma"] = mad["Close"].ewm(9).mean()
mad["21ma"] = mad["Close"].ewm(21).mean()

sql = """
        select
            *
        from
            bitflyer_btc_ohlc_1M
        WHERE
                minute(Date) = 55
            or  minute(Date) between 0 and 1
            or  minute(Date) = 28
        order by
            Date
        """
hod = repository.read_sql(database=database, sql=sql)

profits = []
for i in range(len(hod)):
    latest = hod.iloc[i]
    latest_date = latest["Date"]
    latest_minute = latest_date.minute

    print(latest_date, int(asset))

    if latest_minute == 0:
        if (i - 1) < 0:
            continue
        if (i + 2) > len(hod) - 1:
            break

        fr = hod.iloc[i - 1]
        to = latest
        entry = hod.iloc[i + 1]
        close = hod.iloc[i + 2]

        fr_date = fr["Date"]
        fr_add_date = fr_date + datetime.timedelta(hours=1)
        to_date = to["Date"]
        entry_date = entry["Date"]
        close_date = close["Date"]

        if fr_add_date.hour != to_date.hour or to_date.hour != entry_date.hour or entry_date.hour != close_date.hour \
                or fr_date.minute != 55 or entry_date.minute != 1 or close_date.minute != 28:
            continue

        roc = (to["Close"] - fr["Close"]) / fr["Close"]
        if roc < 0:
            side = "BUY"
        else:
            side = "SELL"

        entry_price = entry["Open"]
        close_price = close["Open"]

        target_mad = mad[to_date <= mad["Date"]]
        target_mad = target_mad[target_mad["Date"] <= close_date]

        for j in range(len(target_mad)):
            if j == 0:
                continue
            if (j + 1) > len(target_mad) - 1:
                break

            before = target_mad.iloc[j - 1]
            now = target_mad.iloc[j]

            before_9ma = before["9ma"]
            before_21ma = before["21ma"]
            now_9ma = now["9ma"]
            now_21ma = now["21ma"]

            crossover = before_9ma <= before_21ma and now_9ma > now_21ma
            crossunder = before_9ma >= before_21ma and now_9ma < now_21ma

            if (side == "BUY" and crossunder) \
                    or (side == "SELL" and crossover):
                close = target_mad.iloc[j + 1]
                close_price = close["Open"]
                break

        amount = asset / entry_price
        if side == "BUY":
            profit = (amount * close_price) - asset
        else:
            profit = asset - (amount * close_price)
        profits.append(profit)
        asset += profit

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

start_date = hod.iloc[0]["Date"]
finish_date = hod.iloc[len(hod) - 1]["Date"]

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
