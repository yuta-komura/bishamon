import datetime
import traceback

import pandas as pd

from lib import bitflyer, indicator, log, repository
from lib.config import Anomaly1, Bitflyer


def non_sfd_fee(side):
    sfd_ratio = bitflyer.get_sfd_ratio()
    if (side == "BUY" and sfd_ratio >= 5) or \
            (side == "SELL" and sfd_ratio <= -5):
        return False
    else:
        return True


def reduce_execution_history():
    first_date = datetime.datetime.now() - datetime.timedelta(minutes=500)
    sql = f"delete from execution_history where date < '{first_date}'"
    repository.execute(database=DATABASE, sql=sql, write=False)


def get_backmin(fr_min, to_min):
    if to_min - fr_min >= 0:
        return to_min - fr_min
    else:
        return to_min + (60 - fr_min)


def get_prices():
    try:
        limit = SMA2
        sql = f"""
        select
            date_format(op.date, '%Y-%m-%d %H:%i:00') as date
            , op.price as price
        from
            (
                select
                    min(id) as open_id
                from
                    execution_history
                group by
                    year (date)
                    , month (date)
                    , day (date)
                    , hour (date)
                    , minute (date)
            ) ba
            inner join execution_history op
                on op.id = ba.open_id
        order by
            date desc
        limit
            {limit}
        """
        df = repository.read_sql(database=DATABASE, sql=sql)
        if len(df) != limit:
            return None
        prices = df.copy()
        prices = df.sort_values("date").reset_index(drop=True).copy()
        prices = indicator.add_rsi(
            df=prices, value=RSI, use_columns="price")
        prices = indicator.add_sma(
            df=prices, value=SMA1, use_columns="price")
        prices = indicator.add_sma(
            df=prices, value=SMA2, use_columns="price")
        prices["date"] = pd.to_datetime(prices["date"])
        prices["price"] = prices["price"].astype(int)
        return prices
    except Exception:
        log.error(traceback.format_exc())


def save_entry(side):
    while True:
        try:
            sql = f"update entry set side='{side}'"
            repository.execute(database=DATABASE, sql=sql, write=False)
            log.info(f"{side} entry")
            return
        except Exception:
            log.error(traceback.format_exc())


TRADING_HOUR = Anomaly1.TRADING_HOUR.value
ANALYSIS_FROM_MINUTE = Anomaly1.ANALYSIS_FROM_MINUTE.value
ANALYSIS_TO_MINUTE = Anomaly1.ANALYSIS_TO_MINUTE.value
ENTRY_MINUTE = Anomaly1.ENTRY_MINUTE.value
CLOSE_MINUTE = Anomaly1.CLOSE_MINUTE.value

RSI = Anomaly1.RSI.value
SMA1 = Anomaly1.SMA1.value
SMA2 = Anomaly1.SMA2.value

bitflyer = bitflyer.API(api_key=Bitflyer.Api.value.KEY.value,
                        api_secret=Bitflyer.Api.value.SECRET.value)

DATABASE = "tradingbot"

has_contract = False
while True:
    reduce_execution_history()

    prices = get_prices()
    if prices is None:
        continue
    latest = prices.iloc[len(prices) - 1].copy()
    date = latest["date"]
    hour = date.hour
    minute = date.minute

    if hour in TRADING_HOUR:
        for i in range(len(ENTRY_MINUTE)):
            if minute == ENTRY_MINUTE[i] and not has_contract:

                entry = latest.copy()

                backmin = get_backmin(ANALYSIS_FROM_MINUTE[i], ENTRY_MINUTE[i])
                start_date = date - datetime.timedelta(minutes=backmin)
                td = pd.date_range(start_date, periods=backmin + 1, freq="min")
                fr_date = td[td.minute == ANALYSIS_FROM_MINUTE[i]][0]
                to_date = td[td.minute == ANALYSIS_TO_MINUTE[i]][0]
                entry_date = td[td.minute == ENTRY_MINUTE[i]][0]

                fr_recorde = prices[prices["date"] == fr_date]
                to_recorde = prices[prices["date"] == to_date]

                if fr_recorde.empty or to_recorde.empty:
                    break

                fr_price = fr_recorde["price"].iloc[0]
                to_price = to_recorde["price"].iloc[0]

                if (to_price - fr_price) < 0:
                    side = "BUY"
                    can_trading = entry[f"rsiprice{RSI}"] < 50 \
                        and entry[f"smaprice{SMA1}"] < entry[f"smaprice{SMA2}"]
                else:
                    side = "SELL"
                    can_trading = entry[f"rsiprice{RSI}"] > 50 \
                        and entry[f"smaprice{SMA1}"] > entry[f"smaprice{SMA2}"]

                if can_trading and non_sfd_fee(side=side):
                    save_entry(side=side)
                    has_contract = True

        for i in range(len(CLOSE_MINUTE)):
            if minute == CLOSE_MINUTE[i] and has_contract:
                save_entry(side="CLOSE")
                has_contract = False
