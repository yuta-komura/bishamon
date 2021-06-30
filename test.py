import matplotlib.pyplot as plt

from lib import indicator, math, message
from lib import pandas_option as pd_op
from lib import repository

database = "tradingbot"
pd_op.display_max_columns()
pd_op.display_round_down()

insert_asset = 50000
initial_profit = insert_asset
leverage = 2
asset = initial_profit

rsi = 50

result_data = []

sql = """
        select
            id,
            date,
            case
                when side = 'BUY' then 'SELL'
                when side = 'SELL' then 'BUY'
                else null
            end as side,
            price,
            size
        from
            execution_history_perp
        order by
            date
        """
basis = repository.read_sql(database=database, sql=sql)
basis = indicator.add_rsi(df=basis, value=rsi, use_columns="price")
basis = basis[basis["size"] >= 1]
basis = basis.reset_index()

delete_indexes = []
for i in range(len(basis)):
    if i + 1 > len(basis) - 1:
        break

    price_data = basis.iloc[i]
    next_price_data = basis.iloc[i + 1]

    if price_data["side"] == next_price_data["side"]:
        delete_indexes.append(next_price_data["index"])

trading = basis[~basis["index"].isin(delete_indexes)]
del trading["index"]
trading = trading.reset_index(drop=True)
print(trading)

profits = []
asset_flow = []
for i in range(len(trading)):
    if i + 1 > len(trading) - 1:
        break

    price_data = trading.iloc[i]
    next_price_data = trading.iloc[i + 1]

    entry_date = price_data["date"]
    entry_side = price_data["side"]
    entry_price = price_data["price"]
    entry_indi = price_data[f"rsi{rsi}"]

    close_price = next_price_data["price"]

    amount = (asset * leverage) / entry_price
    if entry_side == "BUY":
        if not entry_indi <= 20:
            continue
        profit = (amount * close_price) - (asset * leverage)
    else:
        if not entry_indi >= 80:
            continue
        profit = (asset * leverage) - (amount * close_price)

    print(entry_date, entry_side)
    profits.append(profit)
    asset += profit
    asset_flow.append(asset)

"""
2021-06-30 17:36:19,316 :: INFO    :: 2021-06-29 04:23:17.555390 〜 2021-06-30 17:35:32.194881 profit 13793 pf 1.63 wp 58 % ic 0.17 trading cnt 217 ('/test.py', 127)

basis["size"] >= 1
rsi20
2021-06-30 17:39:50,326 :: INFO    :: 2021-06-29 04:23:17.555390 〜 2021-06-30 17:39:09.331163 profit 4132 pf 1.8 wp 58 % ic 0.16 trading cnt 65 ('/test.py', 138)
rsi50
2021-06-30 17:42:54,916 :: INFO    :: 2021-06-29 04:23:17.555390 〜 2021-06-30 17:39:09.331163 profit 3998 pf 11.15 wp 78 % ic 0.57 trading cnt 19 ('/test.py', 143)


"""

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

start_date = str(trading.iloc[0]["date"])
finish_date = str(trading.iloc[len(trading) - 1]["date"])

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

fig = plt.figure(figsize=(24, 12), dpi=50)
ax1 = fig.add_subplot(1, 1, 1)
ax1.plot(list(range(len(asset_flow))), asset_flow)
fig.savefig("backtest_result.png")
plt.show()
