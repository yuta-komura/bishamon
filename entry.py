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
has_contract = False
while True:
    historical_price = get_historical_price()
    if historical_price is None:
        continue

    i = len(historical_price) - 1
    latest = historical_price.iloc[i]
    Date = latest["Date"]
    Hour = Date.hour
    Minute = Date.minute

    mentainance_hour = Hour == 4
    if mentainance_hour:
        continue

    if Minute in ENTRY_MINUTE and not has_contract:
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

        has_contract = True

    if Minute in CLOSE_MINUTE and has_contract:
        save_entry(side="CLOSE")

        has_contract = False
