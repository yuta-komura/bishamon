import datetime

import matplotlib.pyplot as plt

from lib import indicator, math
from lib import pandas_option as pd_op
from lib import repository


def calc_profit(analysis_from, analysis_to, entry, close):

    to_price = analysis_to["perp_price"]
    fr_price = analysis_from["perp_price"]
    entry_price = entry["perp_price"]
    close_price = close["perp_price"]

    entry_sfd = entry["sfd"]
    entry_rsi1 = entry[f"rsi{rsi1}"]
    entry_ma_short = entry[f"ma{ma_short}"]
    entry_ma_long = entry[f"ma{ma_long}"]

    if (to_price - fr_price) < 0:
        if entry_sfd >= 5 or \
            (use_rsi1 and entry_rsi1 <= 10) or \
                (use_ma and entry_ma_short > entry_ma_long):
            return 0
        entry_price += entry_price * (spread_ratio / 100)
        close_price -= close_price * (spread_ratio / 100)
        amount = (asset * leverage) / entry_price
        profit = (amount * close_price) - (asset * leverage)
        print(
            "買い",
            entry["date"],
            entry["perp_price"])
    else:
        if entry_sfd <= -5 or \
            (use_rsi1 and entry_rsi1 >= 90) or \
                (use_ma and entry_ma_short < entry_ma_long):
            return 0
        entry_price -= entry_price * (spread_ratio / 100)
        close_price += close_price * (spread_ratio / 100)
        amount = (asset * leverage) / entry_price
        profit = (asset * leverage) - (amount * close_price)
        print(
            "売り",
            entry["date"],
            entry["perp_price"])
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
        order by
            date
        """
basis = repository.read_sql(database=database, sql=sql)
basis = indicator.add_rsi(df=basis, value=rsi1, use_columns="perp_price")
basis = indicator.add_ema(df=basis, value=ma_short, use_columns="perp_price")
basis = indicator.add_ema(df=basis, value=ma_long, use_columns="perp_price")

# basis = basis[basis["date"].between("2021-7-1 08:00:00", "2099-12-31")]
# basis = basis.reset_index(drop=True)

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
              ])]

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

                        profit = calc_profit(
                            analysis_from, analysis_to, entry, close)

                        if profit != 0:
                            profits.append(profit)
                            asset += profit
                            asset_flow.append(asset)
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

                        profit = calc_profit(
                            analysis_from, analysis_to, entry, close)

                        if profit != 0:
                            profits.append(profit)
                            asset += profit
                            asset_flow.append(asset)
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

                        profit = calc_profit(
                            analysis_from, analysis_to, entry, close)

                        if profit != 0:
                            profits.append(profit)
                            asset += profit
                            asset_flow.append(asset)
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

print(basis)
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

print("trading回数", len(profits))

fig = plt.figure(figsize=(24, 12), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
fig.savefig("backtest_result.png")
plt.show()
