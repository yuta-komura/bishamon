import datetime

import matplotlib.pyplot as plt

from lib import math
from lib import pandas_option as pd_op
from lib import repository

database = "tradingbot"
pd_op.display_max_columns()
pd_op.display_round_down()

do_deposit = True

analysis_from_time = 55
analysis_to_time = 0
entry_time = 1
close_time = 18

print("parameter : ")
print(f"analysis_from_time {analysis_from_time}")
print(f"analysis_to_time {analysis_to_time}")
print(f"entry_time {entry_time}")
print(f"close_time {close_time}")

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
            (minute(perp.date) = {analysis_from_time}
            or minute(perp.date) = {analysis_to_time}
            or minute(perp.date) = {entry_time}
            or minute(perp.date) = {close_time})
            # and perp.date between '2021-04-15 00:00:00' and '2099-04-30 00:00:00'
        order by
            date
        """
data_prices = repository.read_sql(database=database, sql=sql)

print(data_prices)

profits = []
asset_flow = []
for i in range(len(data_prices)):
    if i - 1 >= 0:
        before_data_month = data_prices.iloc[i - 1]["date"].month
        now_data_month = data_prices.iloc[i]["date"].month
        if do_deposit and before_data_month != now_data_month:
            asset += insert_asset

        data_price = data_prices.iloc[i]
        if data_price["date"].hour != 4 and data_price["date"].minute == 0:

            if i + 2 <= len(data_prices) - 1:
                analysis_from = data_prices.iloc[i - 1]
                analysis_to = data_price
                data_entry = data_prices.iloc[i + 1]
                data_close = data_prices.iloc[i + 2]

                if (analysis_from["date"] + datetime.timedelta(hours=1)).hour == analysis_to["date"].hour \
                        and analysis_to["date"].hour == data_entry["date"].hour \
                        and data_entry["date"].hour == data_close["date"].hour:
                    if analysis_from["date"].minute == analysis_from_time \
                            and data_entry["date"].minute == entry_time \
                            and data_close["date"].minute == close_time:
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
                        else:
                            if entry_sfd <= -5:
                                continue
                            profit = (asset * leverage) - \
                                (amount * close_price)

                        profits.append(profit)
                        asset += profit
                        asset_flow.append(asset)

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
fig.savefig("backtest_result.png")
plt.show()
