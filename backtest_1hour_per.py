import datetime

import matplotlib.pyplot as plt

from lib import math
from lib import pandas_option as pd_op
from lib import repository


def calc_profit(analysis_from, analysis_to, entry, close):

    to_price = analysis_to["perp_price"]
    fr_price = analysis_from["perp_price"]
    entry_price = entry["perp_price"]
    close_price = close["perp_price"]

    entry_sfd = entry["sfd"]

    if (to_price - fr_price) < 0:
        if entry_sfd >= 5:
            return 0
        entry_price += entry_price * (spread_ratio / 100)
        close_price -= close_price * (spread_ratio / 100)
        amount = (asset * leverage) / entry_price
        profit = (amount * close_price) - \
            (asset * leverage)
    else:
        if entry_sfd <= -5:
            return 0
        entry_price -= entry_price * (spread_ratio / 100)
        close_price += close_price * (spread_ratio / 100)
        amount = (asset * leverage) / entry_price
        profit = (asset * leverage) - \
            (amount * close_price)
    return profit


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
    if(len(price) > 1 and price[0:2] == "-,"):
        price = "-" + price[2:]
    return price


database = "tradingbot"
pd_op.display_max_columns()
pd_op.display_round_down()

insert_asset = 50000
# spread_ratio = 0.0016  # 0.0008 * 2
spread_ratio = 0
do_deposit = False

analysis_from_minutes1 = 51
analysis_to_minutes1 = 0
entry_minutes1 = 1
close_minutes1 = 18

analysis_from_minutes2 = 1
analysis_to_minutes2 = 13
entry_minutes2 = 20
close_minutes2 = 36

analysis_from_minutes3 = 17
analysis_to_minutes3 = 29
entry_minutes3 = 45
close_minutes3 = 49

initial_profit = insert_asset
leverage = 2

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
            minute(perp.date) = {analysis_from_minutes1}
            or minute(perp.date) = {analysis_to_minutes1}
            or minute(perp.date) = {entry_minutes1}
            or minute(perp.date) = {close_minutes1}

            or minute(perp.date) = {analysis_from_minutes2}
            or minute(perp.date) = {analysis_to_minutes2}
            or minute(perp.date) = {entry_minutes2}
            or minute(perp.date) = {close_minutes2}

            or minute(perp.date) = {analysis_from_minutes3}
            or minute(perp.date) = {analysis_to_minutes3}
            or minute(perp.date) = {entry_minutes3}
            or minute(perp.date) = {close_minutes3}
            )
            # and perp.date between '2021-06-01 00:00:00' and '2099-04-30 00:00:00'
        order by
            date
        """
data_prices = repository.read_sql(database=database, sql=sql)

for j in range(0, 24):

    asset = initial_profit
    test_hour = j

    profits = []
    asset_flow = []
    p = 0
    for i in range(len(data_prices)):

        try:
            before_data_month = data_prices.iloc[i - 1]["date"].month
            now_data_month = data_prices.iloc[i]["date"].month
            if do_deposit and before_data_month != now_data_month:
                asset += insert_asset

            data_price = data_prices.iloc[i]

            if data_price["date"].hour != test_hour:
                continue

            if data_price["date"].minute == analysis_to_minutes1:
                if i - 1 > 0:
                    analysis_from = data_prices.iloc[i - 1]
                    analysis_to = data_price
                    entry = data_prices.iloc[i + 1]
                    close = data_prices.iloc[i + 4]

                    if (analysis_from["date"] + datetime.timedelta(hours=1)).hour == analysis_to["date"].hour \
                            and analysis_to["date"].hour == entry["date"].hour \
                            and entry["date"].hour == close["date"].hour:
                        if analysis_from["date"].minute == analysis_from_minutes1 \
                                and entry["date"].minute == entry_minutes1 \
                                and close["date"].minute == close_minutes1:

                            profit = calc_profit(
                                analysis_from, analysis_to, entry, close)

                            if profit != 0:
                                profits.append(profit)
                                p += profit
                                asset_flow.append(p)
                continue

            if data_price["date"].minute == analysis_to_minutes2:
                if i - 1 > 0:
                    analysis_from = data_prices.iloc[i - 1]
                    analysis_to = data_price
                    entry = data_prices.iloc[i + 3]
                    close = data_prices.iloc[i + 5]

                    if (analysis_from["date"]).hour == analysis_to["date"].hour \
                            and analysis_to["date"].hour == entry["date"].hour \
                            and entry["date"].hour == close["date"].hour:
                        if analysis_from["date"].minute == analysis_from_minutes2 \
                                and entry["date"].minute == entry_minutes2 \
                                and close["date"].minute == close_minutes2:

                            profit = calc_profit(
                                analysis_from, analysis_to, entry, close)

                            if profit != 0:
                                profits.append(profit)
                                p += profit
                                asset_flow.append(p)
                continue

        except Exception as e:
            print(e)

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

    print(f"j : {j}")
    print(start_date, "〜", finish_date, " ")
    print("総利益", add_price_comma(int(sum(profits))), "円  ")
    if pf:
        print("pf", math.round_down(pf, -2), " ")
    if pc:
        print("勝率", math.round_down(pc * 100, 0), "%", " ")
    if ic:
        print("ic", math.round_down(ic, -2), " ")

    print("trading回数", len(profits))

    fig = plt.figure(figsize=(24, 12), dpi=50)
    ax1 = fig.add_subplot(1, 1, 1)
    ax1.plot(list(range(len(asset_flow))), asset_flow)
    fig.savefig(f"backtest_result_{j}.png")
