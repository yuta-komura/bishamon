import datetime

import matplotlib.pyplot as plt
import pandas as pd

from lib import math
from lib import pandas_option as pd_op
from lib import repository

core_asset = 50000
report_path = "/mnt/c/Users/esfgs/bishamon/document/bitflyer/report/Lightning_TradeHistory_20210710.xls"


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
        profit = (amount * close_price) - (asset * leverage)
    else:
        if entry_sfd <= -5:
            return 0
        entry_price -= entry_price * (spread_ratio / 100)
        close_price += close_price * (spread_ratio / 100)
        amount = (asset * leverage) / entry_price
        profit = (asset * leverage) - (amount * close_price)
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


insert_asset = core_asset

pd_op.display_max_columns()
pd_op.display_round_down()

initial_profit = insert_asset
leverage = 2
asset = initial_profit

report = pd.read_excel(report_path, sheet_name=None, index_col=0)
executions = report["Executions 1"].reset_index()
executions = executions[["日時", "売・買", "注文数量", "価格"]]
executions.columns = ["date", "side", "size", "price"]

executions["date"] = executions["date"].replace("/", "-")
executions["date"] = pd.to_datetime(executions["date"])
executions["date"] = executions["date"].dt.strftime("%Y-%m-%d %H:%M:00")
executions["date"] = pd.to_datetime(executions["date"])
executions = executions[(executions["date"].dt.minute == 1) |
                        (executions["date"].dt.minute == 18) |
                        (executions["date"].dt.minute == 20) |
                        (executions["date"].dt.minute == 36) |
                        (executions["date"].dt.minute == 45) |
                        (executions["date"].dt.minute == 49)
                        ]
executions = executions.sort_values("date").reset_index(drop=True)

executions.loc[executions["side"] == "買い", "side"] = "BUY"
executions.loc[executions["side"] == "売り", "side"] = "SELL"

dates = executions.copy()
dates = dates[~dates.duplicated(subset=["date"], keep=False)]
dates = dates[["date"]]

sides = executions.copy()
sides = sides[~sides.duplicated(subset=["date", "side"])]
sides = sides[["date", "side"]]

sizes = executions.copy()
sizes = sizes.groupby("date").sum().reset_index()
sizes = sizes[["date", "size"]]

prices = executions.copy()
prices = prices.groupby("date").mean().reset_index()
prices = prices[["date", "price"]]

executions = pd.merge(dates, sides, on="date", how='inner')
executions = pd.merge(executions, sizes, on="date", how='inner')
executions = pd.merge(executions, prices, on="date", how='inner')
executions = executions[["date", "side", "size", "price"]]
executions = executions.sort_values("date").reset_index(drop=True)

profits = []
asset_flow = []
trading_cnt = 0
fin_entry_dates = []
for i in range(len(executions)):
    if i + 1 > len(executions) - 1:
        break

    entry = executions.iloc[i]
    entry_date = entry["date"]

    close = executions.iloc[i + 1]
    close_date = close["date"]

    if (close_date.month - entry_date.month) >= 1:
        asset += initial_profit

    position_seconds = \
        (close_date - entry_date) / datetime.timedelta(seconds=1)
    position_minutes = int(position_seconds / 60)

    # --------------------------------------------------------- #
    if position_minutes not in [17, 16]:
        continue
    # --------------------------------------------------------- #

    trading_cnt += 1

    fin_entry_dates.append(entry["date"])
    entry_side = entry["side"]
    entry_price = entry["price"]
    close_price = close["price"]

    amount = (asset * leverage) / entry_price
    if entry_side == "BUY":
        profit = (amount * close_price) - (asset * leverage)
    else:  # entry_side == "SELL"
        profit = (asset * leverage) - (amount * close_price)

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

start_date = executions.iloc[0]["date"]
finish_date = executions.iloc[len(executions) - 1]["date"]

print(executions)
print("")

print(start_date, "〜", finish_date, " ")
print("総利益", add_price_comma(int(sum(profits))), "円  ")
if pf:
    print("pf", math.round_down(pf, -2), " ")
if pc:
    print("勝率", math.round_down(pc * 100, 0), "%", " ")
if ic:
    print("ic", math.round_down(ic, -2), " ")

print("trading回数", trading_cnt)
print("")

fig = plt.figure(figsize=(24, 12), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
fig.savefig("backtest_real_result.png")

date_replace = executions["date"].dt.strftime("%Y-%m-%d %H:%M:00")
real_date = pd.to_datetime(date_replace)
real_date = real_date[~real_date.duplicated()].reset_index(drop=True)

database = "tradingbot"
pd_op.display_max_columns()
pd_op.display_round_down()

insert_asset = core_asset
# spread_ratio = 0.0016  # 0.0008 * 2
spread_ratio = 0
MENTAINANCE_HOUR = [3, 4, 5, 6, 7]
do_deposit = True

use_rsi1 = False
rsi1 = 20

use_ma = False
ma_short = 8
ma_long = 21

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
asset = initial_profit

sql = """
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
            perp.date >= '2021-07-01'
        order by
            date
        """
basis = repository.read_sql(database=database, sql=sql)

basis = basis[basis["date"].dt.minute
              .isin([
                    analysis_from_minutes1,
                    analysis_to_minutes1,
                    entry_minutes1,
                    close_minutes1,
                    analysis_from_minutes2,
                    analysis_to_minutes2,
                    entry_minutes2,
                    close_minutes2,
                    analysis_from_minutes3,
                    analysis_to_minutes3,
                    entry_minutes3,
                    close_minutes3
                    ])].reset_index(drop=True)

# basis = basis[basis["date"].between("2021-7-1 00:00:00", "2099-12-31")]
# basis = basis.reset_index(drop=True)

not_executions = basis.copy()
profits = []
asset_flow = []
for i in range(len(basis)):

    try:
        before_data_month = basis.iloc[i - 1]["date"].month
        now_data_month = basis.iloc[i]["date"].month
        if do_deposit and before_data_month != now_data_month:
            asset += insert_asset

        data_price = basis.iloc[i]

        if data_price["date"].hour in MENTAINANCE_HOUR:
            continue

        if data_price["date"].minute == analysis_to_minutes1:
            if i - 1 > 0:
                analysis_from = basis.iloc[i - 1]
                analysis_to = data_price
                entry = basis.iloc[i + 1]
                close = basis.iloc[i + 4]

                if (analysis_from["date"] + datetime.timedelta(hours=1)).hour == analysis_to["date"].hour \
                        and analysis_to["date"].hour == entry["date"].hour \
                        and entry["date"].hour == close["date"].hour:
                    if analysis_from["date"].minute == analysis_from_minutes1 \
                            and entry["date"].minute == entry_minutes1 \
                            and close["date"].minute == close_minutes1:

                        do_test = entry["date"] in fin_entry_dates
                        if not do_test:
                            continue

                        profit = calc_profit(
                            analysis_from, analysis_to, entry, close)

                        if profit != 0:
                            profits.append(profit)
                            asset += profit
                            asset_flow.append(asset)

                            not_executions = \
                                not_executions[not_executions["date"] != entry["date"]]
                            not_executions = \
                                not_executions[not_executions["date"] != close["date"]]
            continue

        if data_price["date"].minute == analysis_to_minutes2:
            if i - 1 > 0:
                analysis_from = basis.iloc[i - 1]
                analysis_to = data_price
                entry = basis.iloc[i + 3]
                close = basis.iloc[i + 5]

                if (analysis_from["date"]).hour == analysis_to["date"].hour \
                        and analysis_to["date"].hour == entry["date"].hour \
                        and entry["date"].hour == close["date"].hour:
                    if analysis_from["date"].minute == analysis_from_minutes2 \
                            and entry["date"].minute == entry_minutes2 \
                            and close["date"].minute == close_minutes2:

                        do_test = entry["date"] in fin_entry_dates
                        if not do_test:
                            continue

                        profit = calc_profit(
                            analysis_from, analysis_to, entry, close)

                        if profit != 0:
                            profits.append(profit)
                            asset += profit
                            asset_flow.append(asset)

                            not_executions = \
                                not_executions[not_executions["date"] != entry["date"]]
                            not_executions = \
                                not_executions[not_executions["date"] != close["date"]]
            continue

        if data_price["date"].minute == analysis_to_minutes3:
            if i - 3 > 0:
                analysis_from = basis.iloc[i - 3]
                analysis_to = data_price
                entry = basis.iloc[i + 2]
                close = basis.iloc[i + 3]

                if (analysis_from["date"]).hour == analysis_to["date"].hour \
                        and analysis_to["date"].hour == entry["date"].hour \
                        and entry["date"].hour == close["date"].hour:
                    if analysis_from["date"].minute == analysis_from_minutes3 \
                            and entry["date"].minute == entry_minutes3 \
                            and close["date"].minute == close_minutes3:

                        do_test = entry["date"] in fin_entry_dates
                        if not do_test:
                            continue

                        profit = calc_profit(
                            analysis_from, analysis_to, entry, close)

                        if profit != 0:
                            profits.append(profit)
                            asset += profit
                            asset_flow.append(asset)

                            not_executions = \
                                not_executions[not_executions["date"] != entry["date"]]
                            not_executions = \
                                not_executions[not_executions["date"] != close["date"]]
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

start_date = basis.iloc[0]["date"]
finish_date = basis.iloc[len(basis) - 1]["date"]

executions = basis[~basis["date"].isin(not_executions["date"])]
executions = executions.reset_index(drop=True)
print(executions)
print("")

print("parameter1 : ")
print(f"analysis_from_minutes1 {analysis_from_minutes1}")
print(f"analysis_to_minutes1 {analysis_to_minutes1}")
print(f"entry_minutes1 {entry_minutes1}")
print(f"close_minutes1 {close_minutes1}")
print("")

print("parameter2 : ")
print(f"analysis_from_minutes2 {analysis_from_minutes2}")
print(f"analysis_to_minutes2 {analysis_to_minutes2}")
print(f"entry_minutes2 {entry_minutes2}")
print(f"close_minutes2 {close_minutes2}")
print("")

print("parameter3 : ")
print(f"analysis_from_minutes3 {analysis_from_minutes3}")
print(f"analysis_to_minutes3 {analysis_to_minutes3}")
print(f"entry_minutes3 {entry_minutes3}")
print(f"close_minutes3 {close_minutes3}")
print("")

print(start_date, "〜", finish_date, " ")
print("総利益", add_price_comma(int(sum(profits))), "円  ")
if pf:
    print("pf", math.round_down(pf, -2), " ")
if pc:
    print("勝率", math.round_down(pc * 100, 0), "%", " ")
if ic:
    print("ic", math.round_down(ic, -2), " ")

print("trading回数", int(len(executions) / 2))

fig = plt.figure(figsize=(24, 12), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
fig.savefig("backtest_result.png")
plt.show()
