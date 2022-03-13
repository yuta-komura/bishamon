import datetime
import sys
import time
import traceback

import pandas as pd
import requests

from lib import bitflyer, indicator, log, repository
from lib.config import Anomaly1, Bitflyer


def non_sfd_fee(side):
    sfd_ratio = bitflyer.get_sfd_ratio()
    if (side == "BUY" and sfd_ratio >= 5) or \
            (side == "SELL" and sfd_ratio <= -5):
        return False
    else:
        return True


def get_backmin(fr_min, to_min):
    if to_min - fr_min >= 0:
        return to_min - fr_min
    else:
        return to_min + (60 - fr_min)


def get_prices():
    while True:
        try:
            sql = "select `key` from coinapi_key where can_use = 1"
            keys = repository.read_sql(database=DATABASE, sql=sql)
            if keys.empty:
                log.error("key lost")
                sys.exit()
            keys = keys["key"].to_list()

            symbol_id = "BITFLYERLTNG_PERP_BTC_JPY"
            period_id = "1MIN"
            limit = SMA2
            url = f"https://rest.coinapi.io/v1/ohlcv/{symbol_id}/latest"
            params = {"period_id": period_id, "limit": limit}
            while True:
                headers = {"X-CoinAPI-Key": keys[0]}
                response = requests.get(
                    url, headers=headers, params=params).json()
                if "error" in response:
                    sql = f"update coinapi_key set can_use=0 where `key`='{keys[0]}'"
                    repository.execute(database=DATABASE, sql=sql, write=False)
                    if len(keys) - 1 <= 0:
                        log.error("key lost")
                        sys.exit()
                    else:
                        del keys[0]
                        continue
                else:
                    break
            response = pd.DataFrame(response)
            if len(response) != limit:
                return None
            prices = response.copy()
            prices["date"] = pd.to_datetime(
                response["time_period_start"],
                utc=True).dt.tz_convert("Asia/Tokyo")
            prices = prices.rename(columns={"price_open": "price"})
            prices = prices[["date", "price"]]
            prices = prices.sort_values("date").reset_index(drop=True)
            prices = indicator.add_rsi(
                df=prices, value=RSI, use_columns="price")
            prices = indicator.add_sma(
                df=prices, value=SMA1, use_columns="price")
            prices = indicator.add_sma(
                df=prices, value=SMA2, use_columns="price")
            prices = prices[limit - 30:].reset_index(drop=True)
            return prices
        except Exception:
            log.error(traceback.format_exc())


def save_entry(side):
    while True:
        try:
            sql = f"update entry set side='{side}'"
            repository.execute(database=DATABASE, sql=sql, write=False)
            return
        except Exception:
            log.error(traceback.format_exc())


TRADING_HOUR = Anomaly1.TRADING_HOUR.value
ANALYSIS_FROM_MINUTE = Anomaly1.ANALYSIS_FROM_MINUTE.value
ANALYSIS_TO_MINUTE = Anomaly1.ANALYSIS_TO_MINUTE.value
ENTRY_MINUTE = Anomaly1.ENTRY_MINUTE.value
CLOSE_MINUTE = Anomaly1.CLOSE_MINUTE.value

RSI = Anomaly1.RSI.value
SMA1 = Anomaly1.SMA1.value
SMA2 = Anomaly1.SMA2.value

bitflyer = bitflyer.API(api_key=Bitflyer.Api.value.KEY.value,
                        api_secret=Bitflyer.Api.value.SECRET.value)

DATABASE = "tradingbot"

has_contract = False
while True:

    date = datetime.datetime.now()
    date = pd.to_datetime(date)
    date = date.tz_localize("Asia/Tokyo")
    date = date.floor("T")
    hour = date.hour
    minute = date.minute

    if hour in TRADING_HOUR:
        for i in range(len(ENTRY_MINUTE)):
            if minute == ENTRY_MINUTE[i] and not has_contract:
                has_contract = True

                backmin = get_backmin(ANALYSIS_FROM_MINUTE[i], ENTRY_MINUTE[i])
                start_date = date - datetime.timedelta(minutes=backmin)
                td = pd.date_range(start_date, periods=backmin + 1, freq="min")
                fr_date = td[td.minute == ANALYSIS_FROM_MINUTE[i]][0]
                to_date = td[td.minute == ANALYSIS_TO_MINUTE[i]][0]
                entry_date = td[td.minute == ENTRY_MINUTE[i]][0]
                print("fr_date", fr_date)
                print("to_date", to_date)
                print("entry_date", entry_date)

                get_prices_cnt = 0
                while True:
                    try:
                        prices = get_prices()
                        entry_recorde = prices[prices["date"] == entry_date]
                        entry = entry_recorde.iloc[0]
                        break
                    except Exception:
                        get_prices_cnt += 1
                        if get_prices_cnt >= 100:
                            log.error("get_prices_cnt >= 100")
                            sys.exit()
                        else:
                            time.sleep(1)

                fr_recorde = prices[prices["date"] == fr_date]
                to_recorde = prices[prices["date"] == to_date]

                print("entry")
                print(entry)
                print("fr_recorde")
                print(fr_recorde)
                print("to_recorde")
                print(to_recorde)

                if fr_recorde.empty or to_recorde.empty:
                    break

                fr_price = fr_recorde["price"].iloc[0]
                to_price = to_recorde["price"].iloc[0]

                if (to_price - fr_price) < 0:
                    side = "BUY"
                    can_trading = entry[f"rsiprice{RSI}"] < 50 \
                        and entry[f"smaprice{SMA1}"] < entry[f"smaprice{SMA2}"]
                else:
                    side = "SELL"
                    can_trading = entry[f"rsiprice{RSI}"] > 50 \
                        and entry[f"smaprice{SMA1}"] > entry[f"smaprice{SMA2}"]

                if can_trading and non_sfd_fee(side=side):
                    save_entry(side=side)

        for i in range(len(CLOSE_MINUTE)):
            if minute == CLOSE_MINUTE[i] and has_contract:
                save_entry(side="CLOSE")
                has_contract = False
