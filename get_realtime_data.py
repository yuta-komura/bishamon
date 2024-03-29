import hmac
import json
import os
import signal
import time
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

public_channels = ['lightning_executions_FX_BTC_JPY']
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
            print("websocket connected")

            if len(self._private_channels) > 0:
                auth(ws)

            if len(self._public_channels) > 0:
                params = [{'method': 'subscribe', 'params': {'channel': c}}
                          for c in self._public_channels]
                ws.send(json.dumps(params))

        def on_error(ws, error):
            print(error)

        def on_close(ws):
            print("websocket closed")

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

            if channel == "lightning_executions_FX_BTC_JPY":
                for r in recept_data:
                    try:
                        date = pd.to_datetime(
                            r["exec_date"]).tz_convert('Asia/Tokyo')
                        side = r["side"]
                        price = r["price"]
                        size = str(r["size"])
                        sql = f"insert into execution_history values (null,'{date}','{side}',{price},'{size}')"
                        cur.execute(sql)
                        print(sql)
                    except Exception:
                        pass

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
    signal.signal(signal.SIGINT, quit_loop)
    ws = bFwebsocket(end_point, public_channels, private_channels, key, secret)
    ws.startWebsocket()
