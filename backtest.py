import datetime

import matplotlib.pyplot as plt
import pandas as pd

from lib import indicator, log, math
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
    if(len(price) > 1 and price[0:2] == "-,"):
        price = "-" + price[2:]
    return price


bet = 50000
leverage = 2
rsi = 1

do_ave_mode = False

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
            # perp.date between '2021-07-12 00:00:00' and '2021-08-10 19:00:00'
        order by
            date
        """

data = repository.read_sql(database=database, sql=sql)
data = indicator.add_rsi(df=data, value=rsi, use_columns="price")

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

if do_ave_mode:
    p1_entries = p1[(p1["date"].dt.minute >= p1_entry) &
                    (p1["date"].dt.minute < p1_close)]
    p1_entries = p1_entries.copy()
    p1_entries["date"] = p1_entries["date"].dt.floor("H")
    p1_entries = p1_entries.groupby(pd.Grouper(key="date", freq="1h")).mean()
    p1_entries = p1_entries.reset_index()
else:
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

if do_ave_mode:
    p2_entries = p2[(p2["date"].dt.minute >= p2_entry) &
                    (p2["date"].dt.minute < p2_close)]
    p2_entries = p2_entries.copy()
    p2_entries["date"] = p2_entries["date"].dt.floor("H")
    p2_entries = p2_entries.groupby(pd.Grouper(key="date", freq="1h")).mean()
    p2_entries = p2_entries.reset_index()
else:
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
tradings = tradings[~((tradings["date"].dt.hour >= 3) &
                      (tradings["date"].dt.hour <= 7))]
tradings = tradings.sort_values("date")

tradings = tradings[~((tradings["side"] == "SELL") & (tradings["sfd"] <= -5))]
tradings = tradings[~((tradings["side"] == "BUY") & (tradings["sfd"] >= 5))]
tradings = tradings[["date", "side", "entry_price", "close_price", "rsi"]]
tradings["amount"] = bet / tradings["entry_price"]

tradings_buy = tradings[tradings["side"] == "BUY"]
tradings_buy = tradings_buy[tradings_buy["rsi"] < 50]
tradings_buy = tradings_buy.copy()
tradings_buy["profit"] = (
    tradings_buy["amount"] * tradings_buy["close_price"]) - bet

tradings_sell = tradings[tradings["side"] == "SELL"]
tradings_sell = tradings_sell[tradings_sell["rsi"] > 50]
tradings_sell = tradings_sell.copy()
tradings_sell["profit"] = bet - \
    (tradings_sell["amount"] * tradings_sell["close_price"])

result = tradings_buy.append(tradings_sell)
result = result[["date", "profit"]]
result = result[(result["date"].dt.hour != 8) &
                (result["date"].dt.hour != 10) &
                (result["date"].dt.hour != 21) &
                (result["date"].dt.hour != 3) &
                (result["date"].dt.hour != 4) &
                (result["date"].dt.hour != 5) &
                (result["date"].dt.hour != 6) &
                (result["date"].dt.hour != 7)]
result = result.sort_values("date")
result = result.reset_index(drop=True)

start_date = result["date"].iloc[0]
end_date = result["date"].iloc[len(result) - 1]

wins = result["profit"][result["profit"] > 0]
loses = result["profit"][result["profit"] < 0]

profit = int(result["profit"].sum() * leverage)
pf = wins.sum() / -(loses.sum())
pf = math.round_down(pf, -2)
wp = len(wins) / (len(wins) + len(loses)) * 100
wp = math.round_down(wp, 0)
cnt = len(result)

log.info(start_date, "～", end_date)
log.info("総利益", add_price_comma(profit), "円")
log.info("pf", pf)
log.info("wp", wp)
log.info("cnt", cnt)

asset_flow = []
p = 0
for i in range(len(result)):
    p += result.iloc[i]["profit"]
    asset_flow.append(p)

fig = plt.figure(figsize=(24, 12), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
fig.savefig("backtest_result.png")
