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
        limit = CHANNEL_BAR_NUM + 1

        sql = """
                select
                    cast(Time as datetime) as Date,
                    Price
                from
                    (
                        select
                            date_format(cast(op.date as datetime), '%Y-%m-%d %H:%i:00') as Time,
                            cl.price as Price
                        from
                            (
                                select
                                    min(id) as open_id,
                                    max(id) as close_id
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
                            inner join
                                execution_history cl
                            on  cl.id = ba.close_id
                    ) as ohlc
                order by
                    Date
                """.format(limit=limit)

        hp = repository.read_sql(database=DATABASE, sql=sql)

        if len(hp) == limit:
            first_Date = hp.loc[0]["Date"]
            sql = "delete from execution_history where date < '{first_Date}'"\
                .format(first_Date=first_Date)
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
    Date = latest["Date"]
    Hour = Date.hour
    Minute = Date.minute

    if Hour in MENTAINANCE_HOUR:
        continue

    if Minute in ENTRY_MINUTE and not has_contract:
        i = 0
        fr = hp.iloc[i]
        fr_Price = fr["Price"]

        i = len(hp) - 2
        to = hp.iloc[i]
        to_Price = to["Price"]

        if (to_Price - fr_Price) < 0:
            side = "BUY"
        else:
            side = "SELL"

        if can_trading(side=side):
            save_entry(side=side)
            has_contract = True

    if Minute in CLOSE_MINUTE and has_contract:
        save_entry(side="CLOSE")

        has_contract = False
