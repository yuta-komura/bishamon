import datetime

import matplotlib.pyplot as plt

from lib import math
from lib import pandas_option as pd_op
from lib import repository


def add_price_comma(price: int) -> str:
    price = str(price)
    rev_price = ''.join(list(reversed(price)))
    add_comma_price = ""
    for i in range(len(rev_price)):
        add_comma_price += rev_price[i]
        if (i + 1) % 3 == 0:
            add_comma_price += ","
    price = ''.join(list(reversed(add_comma_price)))
    if(len(price) > 0 and price[0] == ","):
        price = price[1:]
    return price


database = "tradingbot"
pd_op.display_max_columns()
pd_op.display_round_down()

do_deposit = False

analysis_from_time1 = 51
analysis_to_time1 = 0
entry_time1 = 1
close_time1 = 18

analysis_from_time2 = 17
analysis_to_time2 = 29
entry_time2 = 45
close_time2 = 49

print("parameter1 : ")
print(f"analysis_from_time1 {analysis_from_time1}")
print(f"analysis_to_time1 {analysis_to_time1}")
print(f"entry_time1 {entry_time1}")
print(f"close_time1 {close_time1}")

print("parameter2 : ")
print(f"analysis_from_time2 {analysis_from_time2}")
print(f"analysis_to_time2 {analysis_to_time2}")
print(f"entry_time2 {entry_time2}")
print(f"close_time2 {close_time2}")

insert_asset = 50000
initial_profit = insert_asset
leverage = 2
asset = initial_profit

sql = f"""
        select
            perp.date,
            perp.open as perp_price,
            (perp.open / spot.open - 1) * 100 as sfd
        from
            ohlcv_1min_bitflyer_perp perp
            inner join
                ohlcv_1min_bitflyer_spot spot
            on  perp.date = spot.date
        where
            (
            minute(perp.date) = {analysis_from_time1}
            or minute(perp.date) = {analysis_to_time1}
            or minute(perp.date) = {entry_time1}
            or minute(perp.date) = {close_time1}

            or minute(perp.date) = {analysis_from_time2}
            or minute(perp.date) = {analysis_to_time2}
            or minute(perp.date) = {entry_time2}
            or minute(perp.date) = {close_time2}
            )
            # and perp.date between '2021-06-20 23:00:00' and '2099-04-30 00:00:00'
        order by
            date
        """
data_prices = repository.read_sql(database=database, sql=sql)

print(data_prices)

profits = []
profit_flow = []
now_profit = 0
for i in range(len(data_prices)):
    if i - 1 >= 0:
        before_data_month = data_prices.iloc[i - 1]["date"].month
        now_data_month = data_prices.iloc[i]["date"].month
        if do_deposit and before_data_month != now_data_month:
            asset += insert_asset

        data_price = data_prices.iloc[i]

        if data_price["date"].hour != 4 and data_price["date"].minute == analysis_to_time1:
            if i + 3 <= len(data_prices) - 1:
                analysis_from = data_prices.iloc[i - 1]
                analysis_to = data_price
                data_entry = data_prices.iloc[i + 1]
                data_close = data_prices.iloc[i + 3]

                if (analysis_from["date"] + datetime.timedelta(hours=1)).hour == analysis_to["date"].hour \
                        and analysis_to["date"].hour == data_entry["date"].hour \
                        and data_entry["date"].hour == data_close["date"].hour:
                    if analysis_from["date"].minute == analysis_from_time1 \
                            and data_entry["date"].minute == entry_time1 \
                            and data_close["date"].minute == close_time1:
                        to_price = analysis_to["perp_price"]
                        fr_price = analysis_from["perp_price"]
                        entry_price = data_entry["perp_price"]
                        close_price = data_close["perp_price"]

                        entry_sfd = data_entry["sfd"]

                        amount = (asset * leverage) / entry_price

                        if (to_price - fr_price) < 0:
                            if entry_sfd >= 5:
                                continue
                            profit = (amount * close_price) - \
                                (asset * leverage)
                            print(
                                "買い",
                                data_entry["date"],
                                data_entry["perp_price"])
                        else:
                            if entry_sfd <= -5:
                                continue
                            profit = (asset * leverage) - \
                                (amount * close_price)
                            print(
                                "売り",
                                data_entry["date"],
                                data_entry["perp_price"])

                        profits.append(profit)
                        now_profit += profit
                        profit_flow.append(now_profit)

        if data_price["date"].hour != 4 and data_price["date"].minute == analysis_to_time2:
            if i + 2 <= len(data_prices) - 1:
                analysis_from = data_prices.iloc[i - 2]
                analysis_to = data_price
                data_entry = data_prices.iloc[i + 1]
                data_close = data_prices.iloc[i + 2]

                if (analysis_from["date"]).hour == analysis_to["date"].hour \
                        and analysis_to["date"].hour == data_entry["date"].hour \
                        and data_entry["date"].hour == data_close["date"].hour:
                    if analysis_from["date"].minute == analysis_from_time2 \
                            and data_entry["date"].minute == entry_time2 \
                            and data_close["date"].minute == close_time2:
                        to_price = analysis_to["perp_price"]
                        fr_price = analysis_from["perp_price"]
                        entry_price = data_entry["perp_price"]
                        close_price = data_close["perp_price"]

                        entry_sfd = data_entry["sfd"]

                        amount = (asset * leverage) / entry_price

                        if (to_price - fr_price) < 0:
                            if entry_sfd >= 5:
                                continue
                            profit = (amount * close_price) - \
                                (asset * leverage)
                            print(
                                "買い",
                                data_entry["date"],
                                data_entry["perp_price"])
                        else:
                            if entry_sfd <= -5:
                                continue
                            profit = (asset * leverage) - \
                                (amount * close_price)
                            print(
                                "売り",
                                data_entry["date"],
                                data_entry["perp_price"])

                        profits.append(profit)
                        now_profit += profit
                        profit_flow.append(now_profit)

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

start_date = data_prices.iloc[0]["date"]
finish_date = data_prices.iloc[len(data_prices) - 1]["date"]

print(start_date, "〜", finish_date)
print("profit", add_price_comma(int(sum(profits))))
if pf:
    print("pf", math.round_down(pf, -2))
if pc:
    print("wp", math.round_down(pc * 100, 0), "%")
if ic:
    print("ic", math.round_down(ic, -2))

print("trading cnt", len(profits))

fig = plt.figure(figsize=(24, 12), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(profit_flow))), profit_flow)
fig.savefig("backtest_result.png")
plt.show()
