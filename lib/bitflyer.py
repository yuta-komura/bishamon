import time
import traceback
from decimal import Decimal

import pybitflyer

from lib import log, math, repository


class API:

    def __init__(self, api_key, api_secret):
        self.api = pybitflyer.API(api_key=api_key, api_secret=api_secret)
        self.PRODUCT_CODE = "FX_BTC_JPY"
        self.LEVERAGE = Decimal("2")
        self.DATABASE = "tradingbot"
        self.NORMAL_ORDER_SIZE = Decimal("0.01")

    def order(self, side):
        log.info(side, "order start")
        try:
            while True:
                response = \
                    self.__send_order(side=side, size=self.NORMAL_ORDER_SIZE)
                if "child_order_acceptance_id" not in response:
                    log.info(side, "order complete")
                    return
                time.sleep(2)
        except Exception:
            log.error(traceback.format_exc())

    def close(self):
        log.info("CLOSE start")
        try:
            while True:
                position = self.__get_position()

                has_completed_close = position["size"] < 0.000001
                if has_completed_close:
                    log.info("CLOSE complete")
                    return

                side = self.__reverse_side(side=position["side"])
                order_num = int(position["size"] / self.NORMAL_ORDER_SIZE) - 1
                for _ in range(order_num):
                    self.__send_order(side=side, size=self.NORMAL_ORDER_SIZE)
                    time.sleep(2)

                ordered_size = Decimal(str(order_num)) * self.NORMAL_ORDER_SIZE
                remaining_size = position["size"] - ordered_size
                self.__send_order(side=side, size=remaining_size)
                time.sleep(2)
        except Exception:
            log.error(traceback.format_exc())

    def __reverse_side(self, side):
        return "SELL" if side == "BUY" else "BUY"

    def __send_order(self, side, size):
        try:
            side, size = self.__order_normalize(side=side, size=size)
            response = self.api.sendchildorder(
                product_code=self.PRODUCT_CODE,
                child_order_type="MARKET",
                side=side,
                size=size,
                minute_to_expire=1,
                time_in_force="GTC"
            )
            log.info("sendchildorder", f"side={side}, size={size}")
            return response
        except Exception:
            log.error(traceback.format_exc())

    @staticmethod
    def __order_normalize(side, size):
        size = float(math.round_down(size, -6))
        return side, size

    def __get_order_size(self, price, position_size):
        collateral = None
        try:
            collateral = self.api.getcollateral()
            collateral = Decimal(str(collateral["collateral"]))
            price = Decimal(str(price))
            position_size = Decimal(str(position_size))

            valid_size = (collateral * self.LEVERAGE) / price
            size = valid_size - position_size
            size = size - Decimal("0.000001")
            return size
        except Exception:
            log.error(traceback.format_exc())
            log.error("collateral", collateral)

    def __get_order_price(self, side):
        ticker = self.__get_best_price()

        """
        order book

                0.03807971 1233300
                0.13777962 1233297
                0.10000000 1233288 ticker["best_ask"]
        ticker["best_bid"] 1233218 0.05000000
                            1233205 0.07458008
                            1233201 0.02000000

        sell order price -> ticker["best_ask"] - 1 : 1233287
        buy  order price -> ticker["best_bid"] + 1 : 1233219
        """

        if side == "BUY":
            return int(ticker["best_bid"] + 1)
        else:  # side == "SELL"
            return int(ticker["best_ask"] - 1)

    def __get_position(self):
        positions = None
        try:
            positions = \
                self.api.getpositions(product_code=self.PRODUCT_CODE)

            side = None
            size = Decimal("0")
            for position in positions:
                side = position["side"]
                size += Decimal(str(position["size"]))

            return {"side": side, "size": size}
        except Exception:
            log.error(traceback.format_exc())
            log.error("positions", positions)

    def __get_best_price(self):
        ticker = None
        try:
            ticker = self.__get_ticker()
            best_ask = int(ticker["best_ask"])
            best_bid = int(ticker["best_bid"])
            return {"best_ask": best_ask, "best_bid": best_bid}
        except Exception:
            log.error(traceback.format_exc())
            log.error("ticker", ticker)

    def __get_ticker(self):
        try:
            return self.api.ticker(product_code=self.PRODUCT_CODE)
        except Exception:
            log.error(traceback.format_exc())

    def get_sfd_ratio(self):
        try:
            btcjpy_ltp = self.api.ticker(product_code="BTC_JPY")["ltp"]
            fxbtcjpy_ltp = self.__get_ticker()["ltp"]
            sfd_ratio = (fxbtcjpy_ltp / btcjpy_ltp - 1) * 100
            sfd_ratio = float(math.round_down(sfd_ratio, -2))
            return sfd_ratio
        except Exception:
            log.error(traceback.format_exc())
            log.error("btcjpy_ltp", btcjpy_ltp)
            log.error("fxbtcjpy_ltp", fxbtcjpy_ltp)

    def __cancelallchildorders(self):
        self.api.cancelallchildorders(product_code=self.PRODUCT_CODE)

    def __has_changed_side(self, side):
        try:
            sql = "select * from entry"
            entry = \
                repository.read_sql(database=self.DATABASE, sql=sql)
            if entry.empty:
                log.error("entry empty")
                return True
            latest_side = entry.at[0, "side"]
            if latest_side != side:
                log.info("change side from", side, "to", latest_side)
                return True
            else:
                return False
        except Exception:
            return False
