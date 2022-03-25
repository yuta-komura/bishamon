import datetime
import time
import traceback

from lib import bitflyer, log, repository
from lib.config import Bitflyer


def get_side():
    try:
        sql = "select * from entry"
        entry = repository.read_sql(database=DATABASE, sql=sql)
        if entry.empty:
            return None
        else:
            return entry.at[0, "side"]
    except Exception:
        log.error(traceback.format_exc())
        return None


bitflyer = bitflyer.API(api_key=Bitflyer.Api.value.KEY.value,
                        api_secret=Bitflyer.Api.value.SECRET.value)

DATABASE = "tradingbot"

latest_side = None
while True:
    side = get_side()
    if side is None:
        continue

    date = datetime.datetime.now()
    if side == "CLOSE" and date.second == 30:
        time.sleep(1)
        bitflyer.close()

    if side != latest_side:
        if side == "CLOSE":
            bitflyer.close()
        else:  # side is BUY or SELL
            bitflyer.order(side=side)

        latest_side = side
