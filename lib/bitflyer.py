import time
import traceback

import pybitflyer

from lib import math, message, repository


class API:

    def __init__(self, api_key, api_secret):
        self.api = pybitflyer.API(api_key=api_key, api_secret=api_secret)
        self.PRODUCT_CODE = "FX_BTC_JPY"
        self.LEVERAGE = 2
        self.DATABASE = "tradingbot"

    def order(self, side):
        message.info(side, "order start")
        while True:
            try:
                self.__cancelallchildorders()

                position = self.__get_position()

                has_position = position["side"] is not None
                should_close = has_position \
                    and (side != position["side"] and position["size"] >= 0.01)
                if should_close:
                    self.close()
                    continue

                price = self.__get_order_price(side=side)

                size = self.__get_order_size(price=price,
                                             position_size=position["size"])

                has_completed_order = size < 0.01 \
                    or self.__has_changed_side(side=side)
                if has_completed_order:
                    message.info(side, "order complete")
                    return

                self.__send_order(side=side, size=size, price=price)

                time.sleep(1)
            except Exception:
                message.error(traceback.format_exc())
                time.sleep(3)

    def close(self):
        message.info("close start")
        while True:
            try:
                self.__cancelallchildorders()

                position = self.__get_position()

                has_completed_close = \
                    position["side"] is None or position["size"] < 0.01
                if has_completed_close:
                    message.info("close complete")
                    return

                side = self.__reverse_side(side=position["side"])
                size = position["size"]
                price = self.__get_order_price(side=side)

                self.__send_order(side=side, size=size, price=price)

                time.sleep(1)
            except Exception:
                message.error(traceback.format_exc())
                time.sleep(3)

    def __reverse_side(self, side):
        if side == "BUY":
            return "SELL"
        if side == "SELL":
            return "BUY"

    def __send_order(self, side, size, price):
        try:
            side, size, price = \
                self.__order_normalize(side=side, size=size, price=price)

            self.api.sendchildorder(
                product_code=self.PRODUCT_CODE,
                child_order_type="LIMIT",
                side=side,
                size=size,
                price=price,
                minute_to_expire=1,
                time_in_force="GTC"
            )

            sendchildorder_content = \
                "side={side}, size={size}, price={price}"\
                .format(side=side, size=size, price=price)
            message.info("sendchildorder", sendchildorder_content)
        except Exception:
            message.error(traceback.format_exc())
            time.sleep(3)

    @staticmethod
    def __order_normalize(side, size, price):
        side = str(side)
        size = float(math.round_down(size, -2))
        price = int(price)
        return side, size, price

    def __get_order_size(self, price, position_size):
        collateral = None
        while True:
            try:
                collateral = self.api.getcollateral()

                collateral = collateral["collateral"]
                valid_size = (collateral * self.LEVERAGE) / price
                size = (valid_size - position_size) - 0.01
                return size
            except Exception:
                message.error(traceback.format_exc())
                message.error("collateral", collateral)
                time.sleep(3)

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
        while True:
            try:
                positions = \
                    self.api.getpositions(product_code=self.PRODUCT_CODE)

                side = None
                size = 0
                for position in positions:
                    side = position["side"]
                    size += position["size"]

                return {"side": side, "size": size}
            except Exception:
                message.error(traceback.format_exc())
                message.error("positions", positions)
                time.sleep(3)

    def __get_best_price(self):
        ticker = None
        while True:
            try:
                ticker = self.__get_ticker()
                best_ask = int(ticker["best_ask"])
                best_bid = int(ticker["best_bid"])
                return {"best_ask": best_ask, "best_bid": best_bid}
            except Exception:
                message.error(traceback.format_exc())
                message.error("ticker", ticker)
                time.sleep(3)

    def __get_ticker(self):
        try:
            return self.api.ticker(product_code=self.PRODUCT_CODE)
        except Exception:
            message.error(traceback.format_exc())
            time.sleep(3)

    def get_sfd_ratio(self):
        try:
            btcjpy_ltp = self.api.ticker(product_code="BTC_JPY")["ltp"]
            fxbtcjpy_ltp = self.__get_ticker()["ltp"]
            sfd_ratio = (fxbtcjpy_ltp / btcjpy_ltp - 1) * 100
            sfd_ratio = float(math.round_down(sfd_ratio, -2))
            return sfd_ratio
        except Exception:
            message.error(traceback.format_exc())
            message.error("btcjpy_ltp", btcjpy_ltp)
            message.error("fxbtcjpy_ltp", fxbtcjpy_ltp)
            time.sleep(3)

    def __cancelallchildorders(self):
        self.api.cancelallchildorders(product_code=self.PRODUCT_CODE)

    def __has_changed_side(self, side):
        try:
            sql = "select * from entry"
            entry = \
                repository.read_sql(database=self.DATABASE, sql=sql)
            if entry.empty:
                message.error("entry empty")
                return True
            latest_side = entry.at[0, "side"]
            if latest_side != side:
                message.info("change side from", side, "to", latest_side)
                return True
            else:
                return False
        except Exception:
            return False
