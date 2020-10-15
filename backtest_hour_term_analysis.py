import datetime

import matplotlib.pyplot as plt

from lib import math, repository


def get_fr_Date(Date, fr_min):
    d = Date - datetime.timedelta(hours=1)
    return datetime.datetime(
        d.year,
        d.month,
        d.day,
        d.hour,
        fr_min,
        0,
        0)


def get_to_Date(Date):
    return datetime.datetime(
        Date.year,
        Date.month,
        Date.day,
        Date.hour,
        0,
        0,
        0)


def get_entry_Date(Date):
    return datetime.datetime(
        Date.year,
        Date.month,
        Date.day,
        Date.hour,
        1,
        0,
        0)


def get_close_Date(Date, close_min):
    return datetime.datetime(
        Date.year,
        Date.month,
        Date.day,
        Date.hour,
        close_min,
        0,
        0)


database = "tradingbot"

sql = """
        select
            *
        from
            backtest_parameter
        order by
            date
        """
backtest_parameter = repository.read_sql(database=database, sql=sql)
print(backtest_parameter)

for k in range(1, 12):
    asset = 1000000
    profits = []
    profit_flow = []
    profit_sum = 0
    for i in range(len(backtest_parameter)):
        try:
            data = backtest_parameter.iloc[i]
            Date = data["date"]

            fr_mins = []
            close_mins = []
            is_invalid = False
            for j in range(0, k):
                if i - j < 0:
                    is_invalid = True
                    break
                data = backtest_parameter.iloc[i - j]
                fr_min = data["fr_min"]
                close_min = data["close_min"]
                fr_mins.append(fr_min)
                close_mins.append(close_min)

            if is_invalid:
                continue

            fr_min = int(sum(fr_mins) / len(fr_mins))
            close_min = int(sum(close_mins) / len(close_mins))

            fr_Date = get_fr_Date(Date, fr_min) + datetime.timedelta(hours=1)
            to_Date = get_to_Date(Date) + datetime.timedelta(hours=1)
            entry_Date = get_entry_Date(Date) + datetime.timedelta(hours=1)
            close_Date = \
                get_close_Date(Date, close_min) + datetime.timedelta(hours=1)

            sql = """
                    select
                            *
                        from
                            bitflyer_btc_ohlc_1M
                        where
                            Date = '{fr_Date}'
                        or  Date = '{to_Date}'
                        or  Date = '{entry_Date}'
                        or  Date = '{close_Date}'
                    """.format(fr_Date=fr_Date,
                               to_Date=to_Date,
                               entry_Date=entry_Date,
                               close_Date=close_Date)
            test_data = repository.read_sql(database=database, sql=sql)

            if len(test_data) != 4:
                continue

            fr_data = test_data.iloc[0]
            to_data = test_data.iloc[1]
            entry_data = test_data.iloc[2]
            close_data = test_data.iloc[3]

            fr_Date = fr_data["Date"]
            to_Date = to_data["Date"]
            entry_Date = entry_data["Date"]
            close_Date = close_data["Date"]

            fr_Date_add = fr_Date + datetime.timedelta(hours=1)
            if fr_Date_add.hour != to_Date.hour or to_Date.hour != entry_Date.hour or entry_Date.hour != close_Date.hour \
                    or fr_Date.minute != fr_min or to_Date.minute != 0 or entry_Date.minute != 1 or close_Date.minute != close_min:
                continue

            roc = (to_data["Close"] - fr_data["Close"]) / fr_data["Close"]

            entry_Price = entry_data["Open"]
            close_Price = close_data["Open"]

            amount = asset / entry_Price

            if roc < 0:
                profit = (amount * close_Price) - asset
            else:
                profit = asset - (amount * close_Price)

            asset += profit
            profit_flow.append(profit_sum)
            profit_sum += profit
            profits.append(profit)
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

    start_date = backtest_parameter.iloc[0]["date"]
    finish_date = backtest_parameter.iloc[len(backtest_parameter) - 1]["date"]

    horizontal_line = "-------------------------------------------------"
    print(horizontal_line)
    print("k", k)
    print(start_date, "〜", finish_date)
    print("profit", int(sum(profits)))
    if pf:
        print("pf", math.round_down(pf, -2))
    if wp:
        print("wp", math.round_down(wp, 0), "%")
    print("trade_cnt", len(profits))

# fig = plt.figure(figsize=(48, 24), dpi=50)
# ax1 = fig.add_subplot(1, 1, 1)
# ax1.plot(list(range(len(profit_flow))), profit_flow)
# plt.show()
