import datetime
import sys

import matplotlib.pyplot as plt
import pandas as pd

from lib import math
from lib import pandas_option as pd_op


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


insert_asset = 50000
report_path = "/mnt/c/Users/esfgs/bishamon/document/bitflyer/report/Lightning_TradeHistory_20210707.xls"

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
executions = executions[(executions["date"].dt.minute == 45) |
                        (executions["date"].dt.minute == 49)]
executions = executions.sort_values("date").reset_index(drop=True)

executions.loc[executions["side"] == "買い", "side"] = "BUY"
executions.loc[executions["side"] == "売り", "side"] = "SELL"

sides = executions.copy()
sides = sides[~sides.duplicated(subset=["date", "side"])]
sides = sides[["date", "side"]]

sizes = executions.copy()
sizes = sizes.groupby("date").sum().reset_index()
sizes = sizes[["date", "size"]]

prices = executions.copy()
prices = prices.groupby("date").mean().reset_index()
prices = prices[["date", "price"]]

is_valid_size = len(sides) == len(sizes) == len(prices)
if not is_valid_size:
    print("is not valid size")
    sys.exit()

executions = pd.merge(sides, sizes, on="date", how='inner')
executions = pd.merge(executions, prices, on="date", how='inner')
executions = executions[["date", "side", "size", "price"]]
executions = executions.sort_values("date").reset_index(drop=True)

profits = []
asset_flow = []
trading_cnt = 0
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

    if position_seconds != 4:
        continue

    trading_cnt += 1

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

fig = plt.figure(figsize=(24, 12), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
fig.savefig("backtest_real_result.png")
plt.show()
