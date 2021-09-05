import matplotlib.pyplot as plt
import pandas as pd

from lib import math
from lib import pandas_option as pd_op

report_path = "/mnt/c/Users/esfgs/bishamon/document/bitflyer/report/Lightning_TradeHistory_20210831.xls"


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


def normalize_trading(report, entry_min, close_min):
    entries = report.copy()
    entries = entries[["date", "side", "price"]]
    entries = entries[(entries["date"].dt.minute == entry_min)]
    entries = entries.sort_values("date").reset_index(drop=True)
    duplicated_sides = entries[["date"]].duplicated(keep="last")
    entry_sides = entries[~duplicated_sides][["date", "side"]]
    entry_prices = entries.groupby("date").mean().reset_index()
    entries = pd.merge(entry_sides, entry_prices, on="date", how="inner")
    entries["date"] = entries["date"].dt.floor("H")
    entries = entries.rename(columns={"price": "entry_price"})

    closes = report.copy()
    closes = closes[["date", "side", "price"]]
    closes = closes[(closes["date"].dt.minute == close_min)]
    closes = closes.sort_values("date").reset_index(drop=True)
    closes = closes.groupby("date").mean().reset_index()
    closes["date"] = closes["date"].dt.floor("H")
    closes = closes.rename(columns={"price": "close_price"})

    return pd.merge(entries, closes, on="date", how="inner")


bet = 50000
leverage = 2

p1_entry_min = 1
p1_close_min = 18

p2_entry_min = 20
p2_close_min = 36

pd_op.display_max_columns()
pd_op.display_round_down()

leverage = 2

report = pd.read_excel(report_path, sheet_name=None, index_col=0)

report = report["Executions 1"].reset_index()
report = report[["日時", "売・買", "注文数量", "価格"]]
report.columns = ["date", "side", "size", "price"]

report["date"] = report["date"].replace("/", "-")
report["date"] = pd.to_datetime(report["date"])
report["date"] = report["date"].dt.strftime("%Y-%m-%d %H:%M:00")
report["date"] = pd.to_datetime(report["date"])
report.loc[report["side"] == "買い", "side"] = "BUY"
report.loc[report["side"] == "売り", "side"] = "SELL"
# report = report[report["date"] >= '2021-07-12 00:00:00']
report = report.sort_values("date")
report = report.reset_index(drop=True)

p1_tradings = normalize_trading(report, p1_entry_min, p1_close_min)
p2_tradings = normalize_trading(report, p2_entry_min, p2_close_min)

tradings = p1_tradings.append(p2_tradings)
tradings = tradings[~((tradings["date"].dt.hour >= 3) &
                      (tradings["date"].dt.hour <= 7))]
tradings = tradings.sort_values("date")
tradings = tradings.reset_index(drop=True)

tradings["amount"] = bet / tradings["entry_price"]

tradings_buy = tradings[tradings["side"] == "BUY"]
tradings_buy = tradings_buy.copy()
tradings_buy["profit"] = (
    tradings_buy["amount"] * tradings_buy["close_price"]) - bet

tradings_sell = tradings[tradings["side"] == "SELL"]
tradings_sell = tradings_sell.copy()
tradings_sell["profit"] = bet - \
    (tradings_sell["amount"] * tradings_sell["close_price"])


for z in range(0, 24):

    if 3 <= z <= 7:
        continue

    result = tradings_buy.append(tradings_sell)
    result = result[["date", "profit"]]
    result = result.sort_values("date")
    result = result.reset_index(drop=True)
    result = result[result["date"].dt.hour == z]

    wins = result["profit"][result["profit"] > 0]
    loses = result["profit"][result["profit"] < 0]

    profit = int(result["profit"].sum() * leverage)
    pf = wins.sum() / -(loses.sum())
    pf = math.round_down(pf, -2)
    wp = len(wins) / (len(wins) + len(loses)) * 100
    wp = math.round_down(wp, 0)
    cnt = len(result)

    start_date = result.iloc[0]["date"]
    end_date = result.iloc[len(result) - 1]["date"]

    print("----------------------------------")
    print(z, "時")

    print(start_date, "～", end_date)
    print("総利益", add_price_comma(profit), "円")
    print("pf", pf)
    print("wp", wp)
    print("cnt", cnt)

    # asset_flow = []
    # p = 0
    # for i in range(len(result)):
    #     p += result.iloc[i]["profit"]
    #     asset_flow.append(p)

    # fig = plt.figure(figsize=(24, 12), dpi=50)
    # ax1 = fig.add_subplot(1, 1, 1)
    # ax1.plot(list(range(len(asset_flow))), asset_flow)
    # fig.savefig(f"{z}.png")
