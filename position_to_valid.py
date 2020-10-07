import traceback

from lib import bitflyer, message, repository
from lib.config import Bitflyer

bitflyer = bitflyer.API(api_key=Bitflyer.Api.value.KEY.value,
                        api_secret=Bitflyer.Api.value.SECRET.value)

DATABASE = "tradingbot"
latest_date = None
while True:
    try:
        sql = "select * from position"
        position = repository.read_sql(database=DATABASE, sql=sql)
        if position.empty:
            continue
        position = position.iloc[0]
        date = position["date"]
        side = position["side"]
        size = position["size"]
    except Exception:
        message.error(traceback.format_exc())
        continue

    if latest_date is None \
            or latest_date != date:
        bitflyer.position_validation(order_side=side, order_size=size)
        latest_date = date
