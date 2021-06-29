from lib import bitflyer, message, repository
from lib.config import Anomaly, Bitflyer, HistoricalPrice, Trading


def can_trading(side):
    sfd_ratio = bitflyer.get_sfd_ratio()
    if (side == "BUY" and sfd_ratio >= 5) or (
            side == "SELL" and sfd_ratio <= -5):
        return False
    else:
        return True


def get_historical_price():
    try:
        limit = CHANNEL_BAR_NUM

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
                                limit {limit}
                            ) ba
                            inner join
                                execution_history op
                            on  op.id = ba.open_id
                    ) as ohlc
                order by
                    date
                """.format(limit=limit)

        hp = repository.read_sql(database=DATABASE, sql=sql)

        if len(hp) == limit:
            first_date = hp.loc[0]["date"]
            sql = "delete from execution_history where date < '{first_date}'"\
                .format(first_date=first_date)
            repository.execute(database=DATABASE, sql=sql, write=False)
            return hp
        else:
            return None
    except Exception:
        return None


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

TIME_FRAME = HistoricalPrice.TIME_FRAME.value
CHANNEL_WIDTH = HistoricalPrice.CHANNEL_WIDTH.value
CHANNEL_BAR_NUM = TIME_FRAME * CHANNEL_WIDTH

MENTAINANCE_HOUR = Trading.MENTAINANCE_HOUR.value

bitflyer = bitflyer.API(api_key=Bitflyer.Api.value.KEY.value,
                        api_secret=Bitflyer.Api.value.SECRET.value)

DATABASE = "tradingbot"

Minute = None
has_contract = False
while True:
    hp = get_historical_price()
    if hp is None:
        continue

    i = len(hp) - 1
    latest = hp.iloc[i]
    date = latest["date"]
    hour = date.hour
    minute = date.minute

    if hour in MENTAINANCE_HOUR:
        continue

    for i in range(len(ENTRY_MINUTE)):
        if minute == ENTRY_MINUTE[i] and not has_contract:
            fr_recorde = hp[hp["date"].dt.minute == ANALYSIS_FROM_MINUTE[i]]
            if fr_recorde.empty:
                continue

            fr = fr_recorde.iloc[len(fr_recorde) - 1]
            fr_price = fr["price"]

            to_recorde = hp[hp["date"].dt.minute == ANALYSIS_TO_MINUTE[i]]
            if to_recorde.empty:
                continue

            to = to_recorde.iloc[len(to_recorde) - 1]
            to_price = to["price"]

            if (to_price - fr_price) < 0:
                side = "BUY"
            else:
                side = "SELL"

            if can_trading(side=side):
                save_entry(side=side)
                has_contract = True

    for i in range(len(CLOSE_MINUTE)):
        if minute == CLOSE_MINUTE[i] and has_contract:
            save_entry(side="CLOSE")
            has_contract = False
