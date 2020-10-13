import traceback

import pandas as pd

from lib import bitflyer, message, repository
from lib.config import Anomaly, Bitflyer, HistoricalPrice


def get_historical_price() -> pd.DataFrame or None:
    try:
        limit = CHANNEL_BAR_NUM + 1
        historical_price = bitflyer.get_historical_price(limit=limit)
        if len(historical_price) != limit:
            return None
        return historical_price
    except Exception:
        message.error(traceback.format_exc())
        return None


def save_entry(side):
    message.info(side, "entry")
    sql = "update entry set side='{side}'".format(side=side)
    repository.execute(database=DATABASE, sql=sql, write=False)


ENTRY_MINUTE = Anomaly.ENTRY_MINUTE.value
CLOSE_MINUTE = Anomaly.CLOSE_MINUTE.value

TIME_FRAME = HistoricalPrice.TIME_FRAME.value
CHANNEL_WIDTH = HistoricalPrice.CHANNEL_WIDTH.value
CHANNEL_BAR_NUM = TIME_FRAME * CHANNEL_WIDTH

bitflyer = bitflyer.API(api_key=Bitflyer.Api.value.KEY.value,
                        api_secret=Bitflyer.Api.value.SECRET.value)

DATABASE = "tradingbot"

Minute = None
has_signal = False
while True:
    historical_price = get_historical_price()
    if historical_price is None:
        continue

    i = len(historical_price) - 1
    latest = historical_price.iloc[i]
    Date = latest["Date"]
    Hour = Date.hour
    Minute = Date.minute
    Price = latest["Close"]

    can_trading = Hour != 4 or Hour != 5  # 5時 -> pf:0.69, 4時 -> メンテナンス
    if not can_trading:
        continue

    if Minute == ENTRY_MINUTE and not has_signal:
        i = 0
        fr = historical_price.iloc[i]
        fr_Close = fr["Close"]

        i = len(historical_price) - 2
        to = historical_price.iloc[i]
        to_Close = to["Close"]

        roc = (to_Close - fr_Close) / fr_Close

        if roc < 0:
            save_entry(side="BUY")
        else:
            save_entry(side="SELL")

        has_signal = True

    if Minute == CLOSE_MINUTE and has_signal:
        save_entry(side="CLOSE")

        has_signal = False
