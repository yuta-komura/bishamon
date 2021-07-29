import datetime
import sys
import traceback

import pandas as pd

from lib import log
from lib.mysql import MySQL

data_start_date = datetime.datetime(2019, 10, 1)
data_end_date = datetime.datetime(2021, 7, 2)

database = "tradingbot"

data_date = data_start_date
while True:

    conn = MySQL(database=database).conn
    cur = conn.cursor()

    url = f"https://public.bybit.com/trading/BTCUSD/BTCUSD{data_date.strftime('%Y-%m-%d')}.csv.gz"
    executions = pd.read_csv(url)
    executions["date"] = \
        pd.to_datetime(executions["timestamp"],
                       unit='s',
                       utc=True).dt.tz_convert('Asia/Tokyo')
    executions["side"] = executions["side"].str.upper()
    executions = executions.sort_values("date")

    for i in range(len(executions)):
        execution = executions.iloc[i]
        date = execution["date"]
        side = execution["side"]
        price = execution["price"]
        size = execution["size"]
        sql = f"insert into execution_history_bybit values (null,'{date}','{side}','{price}','{size}')"
        try:
            cur.execute(sql)
            print(sql)
        except Exception:
            log.error(traceback.format_exc())

    conn.commit()
    conn.close()
    cur.close()

    data_date += datetime.timedelta(days=1)
    if data_date > data_end_date:
        print("complete")
        sys.exit()
