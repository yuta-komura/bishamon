import datetime
import time
import traceback

from lib import bitflyer, message, repository
from lib.config import Anomaly, Bitflyer

ENTRY_MINUTE = Anomaly.ENTRY_MINUTE.value

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

            message.info("close retry")
            time.sleep(120)
            has_position = bitflyer.close()
            message.info("close retry complete")

            latest_side = side

        else:  # side is BUY or SELL
            order_side, order_size = bitflyer.order(side=side)

            message.info("position retry")
            bitflyer.position_validation(order_side=order_side,
                                         order_size=order_size)
            message.info("position retry complete")

            latest_side = side
