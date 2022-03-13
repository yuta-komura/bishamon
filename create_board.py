import hmac
import json
import os
import signal
import time
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from secrets import token_hex
from threading import Thread

import pandas as pd
import websocket

from lib.config import Bitflyer
from lib.mysql import MySQL

# -------------------------------------
key = Bitflyer.Api.value.KEY.value
secret = Bitflyer.Api.value.SECRET.value

end_point = 'wss://ws.lightstream.bitflyer.com/json-rpc'

public_channels = [
    'lightning_executions_FX_BTC_JPY',
    "lightning_board_FX_BTC_JPY"]

private_channels = []
database = "tradingbot"
# -------------------------------------


def quit_loop(signal, frame):
    os._exit(0)


class bFwebsocket(object):
    def __init__(
            self,
            end_point,
            public_channels,
            private_channels,
            key,
            secret):
        self._end_point = end_point
        self._public_channels = public_channels
        self._private_channels = private_channels
        self._key = key
        self._secret = secret
        self._JSONRPC_ID_AUTH = 1

    def startWebsocket(self):
        def on_open(ws):
            print("Websocket connected")

            if len(self._private_channels) > 0:
                auth(ws)

            if len(self._public_channels) > 0:
                params = [{'method': 'subscribe', 'params': {'channel': c}}
                          for c in self._public_channels]
                ws.send(json.dumps(params))

        def on_error(ws, error):
            print(error)

        def on_close(ws):
            print("Websocket closed")

        def run(ws):
            while True:
                ws.run_forever()
                time.sleep(3)

        def on_message(ws, message):
            messages = json.loads(message)

            if 'id' in messages and messages['id'] == self._JSONRPC_ID_AUTH:
                if 'error' in messages:
                    print('auth error: {}'.format(messages["error"]))
                elif 'result' in messages and messages['result']:
                    params = [{'method': 'subscribe', 'params': {'channel': c}}
                              for c in self._private_channels]
                    ws.send(json.dumps(params))

            if 'method' not in messages or messages['method'] != 'channelMessage':
                return

            params = messages["params"]
            channel = params["channel"]
            recept_data = params["message"]

            if channel == "lightning_board_FX_BTC_JPY":
                sql = "delete from bid where exists (select 1 from mid where bid.price > mid.price)"
                cur.execute(sql)
                sql = "delete from ask where exists (select 1 from mid where ask.price < mid.price)"
                cur.execute(sql)

                asks = recept_data["asks"]
                for a in asks:
                    price = a["price"]
                    size = str(a["size"])
                    sql = f"delete from ask where price = {price}"
                    cur.execute(sql)
                    if Decimal(size) != 0:
                        sql = f"insert into ask values ({price},'{size}')"
                        cur.execute(sql)
                        print(sql)

                bids = recept_data["bids"]
                for b in bids:
                    price = b["price"]
                    size = str(b["size"])
                    sql = f"delete from bid where price = {price}"
                    cur.execute(sql)
                    if Decimal(size) != 0:
                        sql = f"insert into bid values ({price},'{size}')"
                        cur.execute(sql)
                        print(sql)

                price = recept_data["mid_price"]
                sql = f"update mid set price={price}"
                cur.execute(sql)
                print(sql)

            conn.commit()

        def auth(ws):
            now = int(time.time())
            nonce = token_hex(16)
            sign = hmac.new(self._secret.encode(
                'utf-8'), ''.join([str(now), nonce]).encode('utf-8'), sha256).hexdigest()
            params = {
                'method': 'auth',
                'params': {
                    'api_key': self._key,
                    'timestamp': now,
                    'nonce': nonce,
                    'signature': sign},
                'id': self._JSONRPC_ID_AUTH}
            ws.send(json.dumps(params))

        ws = websocket.WebSocketApp(
            self._end_point,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close)
        websocketThread = Thread(target=run, args=(ws, ))
        websocketThread.start()


if __name__ == '__main__':
    conn = MySQL(database=database).conn
    cur = conn.cursor()
    sql = "truncate ask"
    cur.execute(sql)
    sql = "truncate bid"
    cur.execute(sql)
    sql = "truncate mid"
    cur.execute(sql)
    sql = "insert into mid values(0)"
    cur.execute(sql)
    signal.signal(signal.SIGINT, quit_loop)
    ws = bFwebsocket(end_point, public_channels, private_channels, key, secret)
    ws.startWebsocket()