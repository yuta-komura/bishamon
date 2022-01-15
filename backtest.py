import datetime

import matplotlib.pyplot as plt
import pandas as pd

from lib import pandas_option as pd_op
from lib import repository

"""
----------------------------------------------------------
単利パフォーマンス
2019-10-02 06:00:00 ～ 2022-01-15 01:00:00
bet 50,000
総利益 558,576 円
pf 1.4849692157844119
wp 56
cnt 8576
----------------------------------------------------------
複利パフォーマンス
2019-10-02 06:00:00 ～ 2022-01-15 01:00:00
initial_bet 50,000
総利益 1,989,847,419 円
pf 1.492576362877207
wp 56
cnt 8576
"""


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


bet = 50000
leverage = 2

database = "tradingbot"
pd_op.display_max_columns()
pd_op.display_round_down()

p1_fr = 51
p1_to = 0
p1_entry = 1
p1_close = 18

p2_fr = 1
p2_to = 13
p2_entry = 20
p2_close = 36

sql = """
        select
            perp.date,
            perp.open as price,
            (perp.open / spot.open - 1) * 100 as sfd
        from
            ohlcv_1min_bitflyer_perp perp
            inner join
                ohlcv_1min_bitflyer_spot spot
            on  perp.date = spot.date
        # where
            # perp.date between '2021-01-01 00:00:00' and '2099-01-01 00:00:00'
        order by
            date
        """

data = repository.read_sql(database=database, sql=sql)

p1 = data.copy()
p1_frs = p1[p1["date"].dt.minute == p1_fr]
p1_frs = p1_frs.copy()
p1_frs = p1_frs[["date", "price"]]
p1_frs["date"] = p1_frs["date"].dt.floor("H")
p1_frs["date"] = p1_frs["date"] + datetime.timedelta(hours=1)

p1_tos = p1[p1["date"].dt.minute == p1_to]
p1_tos = p1_tos.copy()
p1_tos = p1_tos[["date", "price"]]
p1_tos["date"] = p1_tos["date"].dt.floor("H")

p1_entries = p1[p1["date"].dt.minute == p1_entry]
p1_entries = p1_entries.copy()
p1_entries["date"] = p1_entries["date"].dt.floor("H")

p1_closes = p1[p1["date"].dt.minute == p1_close]
p1_closes = p1_closes.copy()
p1_closes = p1_closes[["date", "price"]]
p1_closes["date"] = p1_closes["date"].dt.floor("H")

p1_tradings = pd.merge(p1_tos, p1_frs, on="date", how="inner")
p1_tradings["side"] = p1_tradings["price_x"] - p1_tradings["price_y"] < 0
p1_tradings["side"] = ["BUY" if s else "SELL" for s in p1_tradings["side"]]
p1_tradings = p1_tradings[["date", "side"]]
p1_tradings = pd.merge(p1_tradings, p1_entries, on="date", how="inner")
p1_tradings = p1_tradings.rename(columns={"price": "entry_price"})
p1_tradings = pd.merge(p1_tradings, p1_closes, on="date", how="inner")
p1_tradings = p1_tradings.rename(columns={"price": "close_price"})

p2 = data.copy()
p2_frs = p2[p2["date"].dt.minute == p2_fr]
p2_frs = p2_frs.copy()
p2_frs = p2_frs[["date", "price"]]
p2_frs["date"] = p2_frs["date"].dt.floor("H")

p2_tos = p2[p2["date"].dt.minute == p2_to]
p2_tos = p2_tos.copy()
p2_tos = p2_tos[["date", "price"]]
p2_tos["date"] = p2_tos["date"].dt.floor("H")

p2_entries = p2[p2["date"].dt.minute == p2_entry]
p2_entries = p2_entries.copy()
p2_entries["date"] = p2_entries["date"].dt.floor("H")

p2_closes = p2[p2["date"].dt.minute == p2_close]
p2_closes = p2_closes.copy()
p2_closes = p2_closes[["date", "price"]]
p2_closes["date"] = p2_closes["date"].dt.floor("H")

p2_tradings = pd.merge(p2_tos, p2_frs, on="date", how="inner")
p2_tradings["side"] = p2_tradings["price_x"] - p2_tradings["price_y"] < 0
p2_tradings["side"] = ["BUY" if s else "SELL" for s in p2_tradings["side"]]
p2_tradings = p2_tradings[["date", "side"]]
p2_tradings = pd.merge(p2_tradings, p2_entries, on="date", how="inner")
p2_tradings = p2_tradings.rename(columns={"price": "entry_price"})
p2_tradings = pd.merge(p2_tradings, p2_closes, on="date", how="inner")
p2_tradings = p2_tradings.rename(columns={"price": "close_price"})

tradings = p1_tradings.append(p2_tradings)

tradings = tradings[~((tradings["side"] == "SELL") & (tradings["sfd"] <= -5))]
tradings = tradings[~((tradings["side"] == "BUY") & (tradings["sfd"] >= 5))]

tradings = tradings[["date", "side", "entry_price", "close_price"]]

tradings["amount"] = bet / tradings["entry_price"]

tradings_buy = tradings[tradings["side"] == "BUY"]
tradings_buy = tradings_buy.copy()
tradings_buy["profit"] = (
    (tradings_buy["amount"] * tradings_buy["close_price"]) - bet) * leverage

tradings_sell = tradings[tradings["side"] == "SELL"]
tradings_sell = tradings_sell.copy()
tradings_sell["profit"] = (
    bet - (tradings_sell["amount"] * tradings_sell["close_price"])) * leverage

result = tradings_buy.append(tradings_sell)
result = result[["date", "profit"]]

#####################################################
# 1 時 pf 1.5164516956966347
# 7 時 pf 1.402583447407872
# 13 時 pf 1.5134861441204566
# 15 時 pf 1.5410675713054829
# 20 時 pf 1.4832743274541111
#####################################################
result = result[(result["date"].dt.hour == 1) |
                (result["date"].dt.hour == 7) |
                (result["date"].dt.hour == 13) |
                (result["date"].dt.hour == 15) |
                (result["date"].dt.hour == 20)]

##############################################################
sql = """
        select
            perp.date,
            perp.open as f_open,
            perp.close as f_close,
            (perp.open / spot.open - 1) * 100 as sfd
        from
            ohlcv_1min_bitflyer_perp perp
            inner join
                ohlcv_1min_bitflyer_spot spot
            on  perp.date = spot.date
        # where
            # perp.date between '2021-01-01 00:00:00' and '2099-01-01 00:00:00'
        order by
            date
        """

data = repository.read_sql(database=database, sql=sql)

history = data.copy()
history["date"] = history["date"].shift(60 * 1)
history["open"] = history["f_open"].shift(60 * 1)
history["close"] = history["f_close"].shift(60 * 1)
history = history.iloc[60 * 1:]
del history["close"]
del history["f_open"]
history = history[["date", "open", "f_close", "sfd"]]
history = history.rename(
    columns={
        "open": "entry_price",
        "f_close": "close_price"})

history = history[history["date"].dt.minute == 0]
history = history[history["sfd"] < 5]

#####################################################
# i 6 pf 1.6479730325205402 wp 56.65829145728644 t_cnt 796
# i 22 pf 1.3534484737044181 wp 53.91414141414141 t_cnt 792
#####################################################
history = history[(history["date"].dt.hour == 6) |
                  (history["date"].dt.hour == 22)]

history["profit"] = (((bet / history["entry_price"]) *
                      history["close_price"]) - bet) * leverage
result2 = history[["date", "profit"]]
result = result.append(result2)
##############################################################

result = result.sort_values("date")
result = result.reset_index(drop=True)

start_date = result["date"].iloc[0]
end_date = result["date"].iloc[len(result) - 1]

cnt = len(result)

wins = result["profit"][result["profit"] > 0]
loses = result["profit"][result["profit"] < 0]

pf = wins.sum() / -loses.sum()
wp = len(wins) / (len(wins) + len(loses)) * 100

asset_flow = []
p = 0
for i in range(len(result)):
    asset_flow.append(p)
    p += result.iloc[i]["profit"]

print("----------------------------------------------------------")
print("単利パフォーマンス")
print(start_date, "～", end_date)
print("bet", add_price_comma(bet))
print("総利益", add_price_comma(int(result["profit"].sum())), "円")
print("pf", pf)
print("wp", int(wp))
print("cnt", cnt)

fig = plt.figure(figsize=(24, 12), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
fig.savefig("backtest_result_単利.png")


asset_flow = []
wins = []
loses = []
initial_bet = bet
for i in range(len(result)):
    asset_flow.append(bet)
    p = (result.iloc[i]["profit"] / initial_bet) * bet
    if p > 0:
        wins.append(p)
    else:
        loses.append(p)
    bet += p

pf = sum(wins) / -sum(loses)

print("----------------------------------------------------------")
print("複利パフォーマンス")
print(start_date, "～", end_date)
print("initial_bet", add_price_comma(initial_bet))
print("総利益", add_price_comma(int(bet)), "円")
print("pf", pf)
print("wp", int(wp))
print("cnt", cnt)

fig = plt.figure(figsize=(24, 12), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
fig.savefig("backtest_result_複利.png")
