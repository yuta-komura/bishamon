import matplotlib.pyplot as plt

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

window = 19
hold = 14

database = "tradingbot"
pd_op.display_max_columns()
pd_op.display_round_down()

sql = """
        select
            perp.date,
            perp.open as price,
            (perp.open + perp.high + perp.low + perp.close) / 4 as p,
            (perp.open / spot.open - 1) * 100 as sfd
        from
            ohlcv_1min_bitflyer_perp perp
            inner join
                ohlcv_1min_bitflyer_spot spot
            on  perp.date = spot.date
        # where
            # perp.date between '2021-03-01 00:00:00' and '2099-06-01 00:00:00'
        order by
            date
        """
basis = repository.read_sql(database=database, sql=sql)

data = basis.copy()
data = indicator.add_rsi(df=data, value=window, use_columns="p")

data["mean"] = data["p"].rolling(window=window).mean()
data["std"] = data["p"].rolling(window=window).std()

data["+1σ"] = data["mean"] + (data["std"] * 1)
data["+2σ"] = data["mean"] + (data["std"] * 2)
data["+3σ"] = data["mean"] + (data["std"] * 3)
data["-1σ"] = data["mean"] - (data["std"] * 1)
data["-2σ"] = data["mean"] - (data["std"] * 2)
data["-3σ"] = data["mean"] - (data["std"] * 3)

data["buy"] = data["price"] < data["-1σ"]
data["sell"] = data["price"] > data["+1σ"]

data = data[(data["buy"]) | (data["sell"])]

data = data.reset_index(drop=True)

has_buy = False
has_sell = False
bbb = 0
sss = 0
entry_price = None
profits = []
asset_flow = []
p = 0
for i in range(len(data)):
    if i - 1 < 0:
        continue

    pr = data.iloc[i - 1]
    trading = data.iloc[i]

    print(trading["date"])

    if pr["buy"] and not has_buy and pr[f"rsi{window}"] < 90:
        bbb += 1
        sss = 0

        has_buy = False
        has_sell = False

        if bbb < hold:
            continue

        if entry_price:
            amount = bet / entry_price
            profit = bet - (amount * trading["price"])
            profits.append(profit)
            asset_flow.append(p)
            p += profit

        entry_price = trading["price"]
        has_buy = True
        has_sell = False

    if pr["sell"] and not has_sell and pr[f"rsi{window}"] > 10:
        sss += 1
        bbb = 0

        has_buy = False
        has_sell = False

        if sss < hold:
            continue

        if entry_price:
            amount = bet / entry_price
            profit = (amount * trading["price"]) - bet
            profits.append(profit)
            asset_flow.append(p)
            p += profit

        entry_price = trading["price"]
        has_buy = False
        has_sell = True

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

start_date = data.iloc[0]["date"]
finish_date = data.iloc[len(data) - 1]["date"]

log.info("-------------------------------------")
log.info("window", window)
log.info("総利益", add_price_comma(int(sum(profits))), "円  ")
if pf:
    log.info("pf", math.round_down(pf, -2), " ")
if pc:
    log.info("勝率", math.round_down(pc * 100, 0), "%", " ")

log.info("trading回数", len(profits))

fig = plt.figure(figsize=(24, 12), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
fig.savefig("backtest_result.png")
