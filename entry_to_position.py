import time

from lib import bitflyer, message, repository
from lib.config import Bitflyer


def has_changed_side(side):
    try:
        sql = "select * from entry"
        entry = \
            repository.read_sql(database=DATABASE, sql=sql)
        if entry.empty:
            message.warning("entry empty")
            return True
        latest_side = entry.at[0, "side"]
        if latest_side != side:
            message.info("change side from", side, "to", latest_side)
            return True
        else:
            return False
    except Exception:
        return False


def retry_sleep(secs: int, side):
    for i in range(secs):
        if has_changed_side(side=side):
            return False
        else:
            time.sleep(1)
    return True


def get_side():
    try:
        sql = "select * from entry"
        entry = repository.read_sql(database=DATABASE, sql=sql)
        if entry.empty:
            return None
        else:
            return entry.at[0, "side"]
    except Exception:
        return None


bitflyer = bitflyer.API(api_key=Bitflyer.Api.value.KEY.value,
                        api_secret=Bitflyer.Api.value.SECRET.value)

DATABASE = "tradingbot"

latest_side = None
while True:
    side = get_side()
    if side is None:
        continue

    if side != latest_side:
        if side == "CLOSE":

            bitflyer.close()

            for i in range(10):
                if retry_sleep(secs=10, side=side):
                    message.info("close retry")
                    bitflyer.close()
                    message.info("close retry complete")
                else:
                    break

            for i in range(60):
                if retry_sleep(secs=30, side=side):
                    message.info("close retry")
                    bitflyer.close()
                    message.info("close retry complete")
                else:
                    break

        else:  # side is BUY or SELL
            bitflyer.order(side=side)

        latest_side = side
