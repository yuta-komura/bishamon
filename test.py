import datetime
import warnings

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as sci

from lib import math, message
from lib import pandas_option as pd_op
from lib import repository

warnings.simplefilter('ignore')
pd_op.display_max_columns()
pd_op.display_round_down()


def get_high_line(df):
    df_high = df.copy()
    while len(df_high) > 3:
        s_line = sci.linregress(x=df_high["no"], y=df_high["high"])
        df_high = df_high.loc[df_high["high"] >
                              s_line[0] * df_high["no"] + s_line[1]]
    if df_high.empty:
        return None
    else:
        return sci.linregress(x=df_high["no"], y=df_high["high"])


def get_low_line(df):
    df_low = df.copy()
    while len(df_low) > 3:
        s_line = sci.linregress(x=df_low["no"], y=df_low["low"])
        df_low = df_low.loc[df_low["low"] <
                            s_line[0] * df_low["no"] + s_line[1]]

    if df_low.empty:
        return None
    else:
        return sci.linregress(x=df_low["no"], y=df_low["low"])


for z in range(1, 20):

    trend_width_min = 70
    challenge_min = 23
    close_min = z

    database = "tradingbot"
    insert_asset = 50000
    initial_profit = insert_asset
    leverage = 2
    asset = initial_profit
    do_deposit = False

    result_data = []

    result_data.append("parameter : ")
    result_data.append(f"trend_width_min {trend_width_min}")
    result_data.append(f"challenge_min {challenge_min}")
    result_data.append(f"close_min {close_min}")

    sql = """
            select
                perp.date,
                perp.open as open,
                perp.high as high,
                perp.low as low,
                perp.close as close,
                ((perp.open / spot.open) - 1) * 100 as sfd
            from
                ohlcv_1min_bitflyer_perp perp
                inner join
                    ohlcv_1min_bitflyer_spot spot
                on  perp.date = spot.date
            where
                perp.date between '2021-01-01 00:00:00' and '2099-01-31 00:00:00'
            order by
                date
            """
    basis = repository.read_sql(database=database, sql=sql)
    basis["no"] = basis.index + 1

    profits = []
    asset_flow = []
    i = 0
    while i + trend_width_min <= len(basis):

        if i - 1 >= 0:
            before_data_month = basis.iloc[i - 1]["date"].month
            now_data_month = basis.iloc[i]["date"].month
            if do_deposit and before_data_month != now_data_month:
                asset += insert_asset

        fr = i
        to = i + trend_width_min
        target = basis[fr:to]

        high_line = get_high_line(target)
        low_line = get_low_line(target)

        if not high_line or not low_line:
            continue

        basis[f"high_line_{i}"] = high_line[0] * basis["no"] + high_line[1]
        basis[f"low_line_{i}"] = low_line[0] * basis["no"] + low_line[1]

        for j in range(challenge_min):
            if to + j + 1 + close_min >= len(basis):
                break
            challenge = basis.iloc[to + j + 1]
            sfd = basis.iloc[(to + j + 1) + 1].sfd

            if challenge["high"] > challenge[f"high_line_{i}"] and sfd < 5:
                position = "BUY"
                entry_price = challenge["close"]

                close = basis.iloc[to + j + 1 + close_min]
                close_price = close["close"]

                amount = (asset * leverage) / entry_price
                profit = (amount * close_price) - (asset * leverage)

                profits.append(profit)
                asset += profit
                asset_flow.append(asset)

                print(str(challenge["date"]),
                      asset,
                      "parameter : ",
                      f"trend_width_min {trend_width_min}",
                      f"challenge_min {challenge_min}",
                      f"close_min {close_min}")

                i = to + j + 1 + close_min
                break

            # if challenge["low"] < challenge[f"low_line_{i}"] and sfd > -5:
            #     position = "SELL"
            #     entry_price = challenge["close"]

            #     close = basis.iloc[to + j + 1 + close_min]
            #     close_price = close["close"]

            #     amount = (asset * leverage) / entry_price
            #     profit = (asset * leverage) - (amount * close_price)

            #     profits.append(profit)
            #     asset += profit
            #     asset_flow.append(asset)

            #     print(str(challenge["date"]),
            #           asset,
            #           "parameter : ",
            #           f"trend_width_min {trend_width_min}",
            #           f"challenge_min {challenge_min}",
            #           f"close_min {close_min}")

            #     i = to + j + 1 + close_min
            #     break

        i += 1
        delete_columns = basis.filter(like="high_line_", axis=1).columns.values
        basis = basis.drop(columns=delete_columns)
        delete_columns = basis.filter(like="low_line_", axis=1).columns.values
        basis = basis.drop(columns=delete_columns)

        if asset < insert_asset * 0.95:
            break

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

    start_date = str(basis.iloc[0]["date"])
    finish_date = str(basis.iloc[len(basis) - 1]["date"])

    result_data.append(start_date)
    result_data.append("〜")
    result_data.append(finish_date)

    result_data.append("profit")
    result_data.append(int(sum(profits)))

    if pf:
        result_data.append("pf")
        result_data.append(math.round_down(pf, -2))
    if pc:
        result_data.append("wp")
        result_data.append(math.round_down(pc * 100, 0))
        result_data.append("%")
    if ic:
        result_data.append("ic")
        result_data.append(math.round_down(ic, -2))

    result_data.append("trading cnt")
    result_data.append(len(profits))

    result_data = str(result_data)
    result_data = result_data.replace("[", "")
    result_data = result_data.replace("]", "")
    result_data = result_data.replace("'", "")
    result_data = result_data.replace(",", "")

    message.info(result_data)

    # fig = plt.figure(figsize=(24, 12), dpi=50)
    # ax1 = fig.add_subplot(1, 1, 1)
    # ax1.plot(list(range(len(asset_flow))), asset_flow)
    # fig.savefig("backtest_result.png")
    # plt.show()
    # break
