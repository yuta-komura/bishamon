import datetime

from lib import bitflyer, log, repository
from lib.config import Anomaly1, Anomaly2, Bitflyer


def non_sfd_fee(side):
    sfd_ratio = bitflyer.get_sfd_ratio()
    if (side == "BUY" and sfd_ratio >= 5) or (
            side == "SELL" and sfd_ratio <= -5):
        return False
    else:
        return True


def reduce_execution_history():
    first_date = datetime.datetime.now() - datetime.timedelta(minutes=30)
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
    df = repository.read_sql(database=DATABASE, sql=sql)
    return df


def save_entry(side):
    log.info(side, "entry")
    while True:
        try:
            sql = "update entry set side='{side}'".format(side=side)
            repository.execute(database=DATABASE, sql=sql, write=False)
            return
        except Exception:
            pass


ANOMALY1_TRADING_HOUR = Anomaly1.TRADING_HOUR.value
ANOMALY1_ANALYSIS_FROM_MINUTE = Anomaly1.ANALYSIS_FROM_MINUTE.value
ANOMALY1_ANALYSIS_TO_MINUTE = Anomaly1.ANALYSIS_TO_MINUTE.value
ANOMALY1_ENTRY_MINUTE = Anomaly1.ENTRY_MINUTE.value
ANOMALY1_CLOSE_MINUTE = Anomaly1.CLOSE_MINUTE.value

ANOMALY2_TRADING_HOUR = Anomaly2.TRADING_HOUR.value

bitflyer = bitflyer.API(api_key=Bitflyer.Api.value.KEY.value,
                        api_secret=Bitflyer.Api.value.SECRET.value)

DATABASE = "tradingbot"

has_contract = False
while True:

    reduce_execution_history()
    hp = get_historical_price()
    if hp.empty:
        break

    latest = hp.iloc[len(hp) - 1]
    date = latest["date"]
    hour = date.hour
    minute = date.minute

    if hour in ANOMALY1_TRADING_HOUR:
        for i in range(len(ANOMALY1_ENTRY_MINUTE)):
            if minute == ANOMALY1_ENTRY_MINUTE[i] and not has_contract:

                fr_recorde = hp[hp["date"].dt.minute ==
                                ANOMALY1_ANALYSIS_FROM_MINUTE[i]]
                if fr_recorde.empty:
                    break
                fr = fr_recorde.iloc[0]
                fr_price = fr["price"]

                to_recorde = hp[hp["date"].dt.minute ==
                                ANOMALY1_ANALYSIS_TO_MINUTE[i]]
                if to_recorde.empty:
                    break
                to = to_recorde.iloc[0]
                to_price = to["price"]

                if (to_price - fr_price) < 0:
                    side = "BUY"
                else:
                    side = "SELL"

                if non_sfd_fee(side=side):
                    save_entry(side=side)

                has_contract = True

        for i in range(len(ANOMALY1_CLOSE_MINUTE)):
            if minute == ANOMALY1_CLOSE_MINUTE[i] and has_contract:
                save_entry(side="CLOSE")
                has_contract = False

    if hour in ANOMALY2_TRADING_HOUR:
        if minute == 0 and not has_contract:
            side = "BUY"
            if non_sfd_fee(side=side):
                save_entry(side=side)

            has_contract = True

        if minute == 59 and has_contract:
            save_entry(side="CLOSE")
            has_contract = False
