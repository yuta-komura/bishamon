import traceback

import pandas as pd

from lib import log
from lib.mysql import MySQL


def read_sql(database: str, sql: str) -> pd.DataFrame:
    conn = MySQL(database=database).conn
    try:
        result = pd.read_sql(sql, conn)
        return result
    except Exception:
        log.error(traceback.format_exc())
    finally:
        conn.close()


def execute(database: str, sql: str, use_log=True, write=True) -> tuple:
    conn = MySQL(database=database).conn
    cur = conn.cursor()
    try:
        cur.execute(sql)
        sql_lower = sql.lower()
        if "select" in sql_lower and "from" in sql_lower:
            result = cur.fetchall()
            return result
        else:
            conn.commit()
            if write:
                if use_log:
                    log.info(sql)
                else:
                    print(sql)
    except Exception:
        log.error(traceback.format_exc())
    finally:
        conn.commit()
        conn.close()
        cur.close()
