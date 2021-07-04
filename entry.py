import datetime
import time

from lib import bitflyer, message, repository
from lib.config import Anomaly, Bitflyer, Trading


def can_trading(side):
    sfd_ratio = bitflyer.get_sfd_ratio()
    if (side == "BUY" and sfd_ratio >= 5) or (
            side == "SELL" and sfd_ratio <= -5):
        return False
    else:
        return True


def reduce_execution_history():
    date = datetime.datetime.now()
    year = date.year
    month = date.month
    day = date.day
    hour = date.hour
    first_date = datetime.datetime(year, month, day, hour, 0, 0, 0)
    sql = f"delete from execution_history where date < '{first_date}'"
    repository.execute(database=DATABASE, sql=sql, write=False)


def get_historical_price():

    sql = """
            select
                cast(date as datetime) as date,
                price
            from
                (
                    select
                        date_format(cast(op.date as datetime), '%Y-%m-%d %H:%i:00') as date,
                        op.price as price
                    from
                        (
                            select
                                min(id) as open_id
                            from
                                execution_history
                            group by
                                year(date),
                                month(date),
                                day(date),
                                hour(date),
                                minute(date)
                            order by
                                max(date) desc
                        ) ba
                        inner join
                            execution_history op
                        on  op.id = ba.open_id
                ) as ohlc
            order by
                date
            """
    return repository.read_sql(database=DATABASE, sql=sql)


def save_entry(side):
    message.info(side, "entry")
    while True:
        try:
            sql = "update entry set side='{side}'".format(side=side)
            repository.execute(database=DATABASE, sql=sql, write=False)
            return
        except Exception:
            pass


ANALYSIS_FROM_MINUTE = Anomaly.ANALYSIS_FROM_MINUTE.value
ANALYSIS_TO_MINUTE = Anomaly.ANALYSIS_TO_MINUTE.value
ENTRY_MINUTE = Anomaly.ENTRY_MINUTE.value
CLOSE_MINUTE = Anomaly.CLOSE_MINUTE.value

MENTAINANCE_HOUR = Trading.MENTAINANCE_HOUR.value

bitflyer = bitflyer.API(api_key=Bitflyer.Api.value.KEY.value,
                        api_secret=Bitflyer.Api.value.SECRET.value)

DATABASE = "tradingbot"

has_contract = False
while True:

    date = datetime.datetime.now()
    hour = date.hour
    minute = date.minute

    if hour in MENTAINANCE_HOUR:
        reduce_execution_history()
        time.sleep(1)
        continue

    for i in range(len(ENTRY_MINUTE)):
        if minute == ENTRY_MINUTE[i] and not has_contract:

            hp = get_historical_price()

            reduce_execution_history()

            if hp.empty:
                break

            fr_recorde = hp[hp["date"].dt.minute == ANALYSIS_FROM_MINUTE[i]]
            if fr_recorde.empty:
                break
            fr = fr_recorde.iloc[0]
            fr_price = fr["price"]

            to_recorde = hp[hp["date"].dt.minute == ANALYSIS_TO_MINUTE[i]]
            if to_recorde.empty:
                break
            to = to_recorde.iloc[0]
            to_price = to["price"]

            if (to_price - fr_price) < 0:
                side = "BUY"
            else:
                side = "SELL"

            if can_trading(side=side):
                save_entry(side=side)
                has_contract = True

            break

    for i in range(len(CLOSE_MINUTE)):
        if minute == CLOSE_MINUTE[i] and has_contract:
            save_entry(side="CLOSE")
            has_contract = False
