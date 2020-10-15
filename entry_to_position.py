import datetime
import time
import traceback

from lib import bitflyer, message, repository
from lib.config import Anomaly, Bitflyer

ENTRY_MINUTE = Anomaly.ENTRY_MINUTE.value
CLOSE_MINUTE = Anomaly.CLOSE_MINUTE.value

bitflyer = bitflyer.API(api_key=Bitflyer.Api.value.KEY.value,
                        api_secret=Bitflyer.Api.value.SECRET.value)

DATABASE = "tradingbot"
latest_side = None
while True:
    try:
        sql = "select * from entry"
        entry = repository.read_sql(database=DATABASE, sql=sql)
        if entry.empty:
            continue
        side = entry.at[0, "side"]
    except Exception:
        message.error(traceback.format_exc())
        continue

    if latest_side is None \
            or latest_side != side:
        if side == "CLOSE":
            bitflyer.close()

            message.info("close validation")

            date = datetime.datetime.now()
            after_sleep_date = date + datetime.timedelta(seconds=180)
            now_to_sleep_list = \
                list(range(date.minute, after_sleep_date.minute + 1))

            reaches_entry_minute = ENTRY_MINUTE in now_to_sleep_list

            if reaches_entry_minute:
                message.warning("sleep reaches entry minute")
                latest_side = side
                continue

            time.sleep(120)

            has_position = bitflyer.close()
            if has_position:
                time.sleep(1)
            else:
                message.info("close is validate")
                latest_side = side

        else:  # side is BUY or SELL
            order_side, order_size = bitflyer.order(side=side)

            message.info("position validation")

            bitflyer.position_validation(order_side=order_side,
                                         order_size=order_size)

            message.info("position is validate")

            latest_side = side
