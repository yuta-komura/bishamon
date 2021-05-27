import datetime

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as sci

from lib import math, message
from lib import pandas_option as pd_op
from lib import repository


def get_high_trend(df):
    df_high = df.copy()
    while len(df_high) > 3:
        s_line = sci.linregress(x=df_high["no"], y=df_high["high"])
        df_high = df_high.loc[df_high["high"] >
                              s_line[0] * df_high["no"] + s_line[1]]
    s_line = sci.linregress(x=df_high["no"], y=df_high["high"])
    return s_line[0] * df["no"] + s_line[1]


def get_low_trend(df):
    df_low = df.copy()
    while len(df_low) > 3:
        s_line = sci.linregress(x=df_low["no"], y=df_low["low"])
        df_low = df_low.loc[df_low["low"] <
                            s_line[0] * df_low["no"] + s_line[1]]
    s_line = sci.linregress(x=df_low["no"], y=df_low["low"])
    return s_line[0] * df["no"] + s_line[1]


database = "tradingbot"
trend_width_min = 10

sql = """
        select
            perp.date,
            perp.open as open,
            perp.high as high,
            perp.low as low,
            perp.close as close,
            (perp.open / spot.open - 1) * 100 as sfd
        from
            ohlcv_1min_bitflyer_perp perp
            inner join
                ohlcv_1min_bitflyer_spot spot
            on  perp.date = spot.date
        order by
            date
        limit 10000
        """
basis = repository.read_sql(database=database, sql=sql)
basis["no"] = basis.index + 1

# fig = plt.figure(figsize=(24, 12), dpi=50)
# ax1 = fig.add_subplot(1, 1, 1)
# ax1.plot(basis["no"], basis["high"], color="red")
# ax1.plot(basis["no"], basis["low"], color="blue")

i = 0
while i + trend_width_min <= len(basis):
    fr = i
    to = i + trend_width_min
    target = basis[fr:to]
    basis[f"high_trend_{i}"] = get_high_trend(target)
    basis[f"low_trend_{i}"] = get_low_trend(target)
    # ax1.plot(basis["no"], basis[f"high_trend_{i}"], color="black")
    # ax1.plot(basis["no"], basis[f"low_trend_{i}"], color="black")
    i = to

plt.show()

# df_high = df.copy()
# while len(df_high) > 3:
#     s_line = sci.linregress(x=df_high["no"], y=df_high["high"])
#     df_high = df_high.loc[df_high["high"] >
#                           s_line[0] * df_high["no"] + s_line[1]]
# s_line = sci.linregress(x=df_high["no"], y=df_high["high"])
# df["high_trend"] = s_line[0] * df["no"] + s_line[1]

# df_low = df.copy()
# while len(df_low) > 3:
#     s_line = sci.linregress(x=df_low["no"], y=df_low["low"])
#     df_low = df_low.loc[df_low["low"] <
#                         s_line[0] * df_low["no"] + s_line[1]]
# s_line = sci.linregress(x=df_low["no"], y=df_low["low"])
# df["low_trend"] = s_line[0] * df["no"] + s_line[1]

# ax1.plot(df["no"], df["high_trend"], "b")
# ax1.plot(df["no"], df["low_trend"], "r")
# ax1.legend()
# plt.show()
