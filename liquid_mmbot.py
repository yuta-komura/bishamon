import datetime
import json
import time

import jwt
import requests
import requests as req

from lib import repository


def get_bf_price():
    sql = "select * from execution_history order by date desc limit 1"
    bf_price = repository.read_sql(database=database, sql=sql).iloc[0]["price"]
    return bf_price


def get_li_price():
    url = "https://api.liquid.com/executions?product_id=5"
    li_price = int(req.get(url=url).json()["models"][0]["price"])
    return li_price


def order_cancel():
    token = "2468075"
    secret = "B779mTSKxYLqkHgifXoATUqt+GxBCjVTndzNfau3D1Io4i00Q1KHO7dZkS85a0YlpbmdCQAJ7/R57lbdLtyUEQ=="
    path = '/orders/cancel_all/'
    query = ''
    url = 'https://api.liquid.com' + path + query
    payload = {
        "path": '/orders/cancel_all/',
        "nonce": str(round(time.time())),
        "token_id": token
    }
    signature = jwt.encode(payload, secret, algorithm='HS256')
    headers = {
        'X-Quoine-API-Version': '2',
        'X-Quoine-Auth': signature,
        'Content-Type': 'application/json'
    }
    data = {
        "order": {
            "trading_type": "spot",
            "product_id": 5
        }
    }
    json_data = json.dumps(data)
    res = requests.put(url, headers=headers, data=json_data)
    datas = json.loads(res.text)
    print("order_cancel")


def order(side, order_prices):
    keys = \
        [["2468075", "B779mTSKxYLqkHgifXoATUqt+GxBCjVTndzNfau3D1Io4i00Q1KHO7dZkS85a0YlpbmdCQAJ7/R57lbdLtyUEQ=="],
         ["2468076", "1KFWvIaDvX+7PDL/lf8ZeB2yXUQcxw0wWlmCD6OZvCsLI9qvTeB1GzLuRW0Dco5N7+129eMfR5DesmkKAr7aVg=="],
         ["2468077", "g8+2pHICYxd2GkcXytY+kDl+n+X4vki2/v6Wv34uACp8MQrUK9WJi8XEs187qH4IvTY838K48E/kSSUaC78hpg=="],
         ["2468078", "ERdPPOrF7Q5dgOfLTcR0miTNL1XkBO9z5eY/3zk/HuvW1F4bN5EZs1INB2xVcTgyDfuBNXuobBYrlMWG8NKegQ=="],
         ["2468079", "ym+5EWKsmUfhbE1I7PCiyFzLdyo59i1/ryd7J43OMPdGi+3ufAx4TbH53EYVbpIUn4NDUnoS6obI1oPPB/fWHQ=="],
         ["2468081", "746tDzPRdyDEcLhPTpyXGSvGkNKpR56HYu/tKdcNtt9RvWOVqfRdKsiILTkUJPUof9IjOx/vi3WJwudLpV2d9g=="],
         ["2468085", "fI5nMe4kmnDRJqxSdV1X7O5HYX7CUPLz1seoWiofGDgQ4U9HICdyAbRp6um3AElJZPCce07jF128t4qOU95HHg=="],
         ["2468086", "tEvET6b2eDXLy0IX/B8WUbYXljVNQL3fjUAeEi6okwwm6EbB/rggsI7iiDk+bBCP0ev1EA16yANUJRKfDRSXFQ=="],
         ["2468088", "dQhOfuQY4179OWdvtowqA2R/MpReY9yhoGUDvtS5gO3bHwH4rWKPW7NUUkracJ2t3lS8DPUX6IVnE+lKepsk+A=="],
         ["2468091", "1RhO9HAqmZOCLqtM2JyYFtVtQvWMvPJ9sYs4SE43X/BQYGL5vSp3ANRRfHKIzDzkxt3+f24uU8C+1eZXLNTAdQ=="]]

    for j in range(len(order_prices)):
        path = '/orders/'
        query = ''
        url = 'https://api.liquid.com' + path + query
        payload = {
            "path": '/orders/',
            "nonce": str(round(time.time())),
            "token_id": keys[j][0]
        }
        signature = jwt.encode(payload, keys[j][1], algorithm='HS256')
        headers = {
            'X-Quoine-API-Version': '2',
            'X-Quoine-Auth': signature,
            'Content-Type': 'application/json'
        }
        data = {
            "order": {
                "order_type": "limit",
                "product_id": 5,
                "side": side,
                "quantity": 0.001,
                "price": order_prices[j]
            }
        }
        json_data = json.dumps(data)
        res = requests.post(url, headers=headers, data=json_data)
        datas = json.loads(res.text)
    print("order")


def close(balance):
    token = "2468075"
    secret = "B779mTSKxYLqkHgifXoATUqt+GxBCjVTndzNfau3D1Io4i00Q1KHO7dZkS85a0YlpbmdCQAJ7/R57lbdLtyUEQ=="
    path = '/orders/'
    query = ''
    url = 'https://api.liquid.com' + path + query
    timestamp = datetime.datetime.now().timestamp()
    payload = {
        "path": '/orders/',
        "nonce": timestamp,
        "token_id": token
    }
    signature = jwt.encode(payload, secret, algorithm='HS256')
    headers = {
        'X-Quoine-API-Version': '2',
        'X-Quoine-Auth': signature,
        'Content-Type': 'application/json'
    }
    data = {
        "order": {
            "order_type": "market",
            "product_id": 5,
            "side": "sell",
            "quantity": balance
        }
    }
    json_data = json.dumps(data)
    res = requests.post(url, headers=headers, data=json_data)
    datas = json.loads(res.text)
    print("close")


def get_balance():
    token = "2468075"
    secret = "B779mTSKxYLqkHgifXoATUqt+GxBCjVTndzNfau3D1Io4i00Q1KHO7dZkS85a0YlpbmdCQAJ7/R57lbdLtyUEQ=="
    path = '/crypto_accounts/'
    query = ''
    url = 'https://api.liquid.com' + path + query
    payload = {
        "path": '/crypto_accounts/',
        "nonce": str(round(time.time())),
        "token_id": token
    }
    signature = jwt.encode(payload, secret, algorithm='HS256')
    headers = {
        'X-Quoine-API-Version': '2',
        'X-Quoine-Auth': signature,
        'Content-Type': 'application/json'
    }
    res = requests.get(url, headers=headers)
    datas = json.loads(res.text)
    balance = datas[0]["balance"]
    print("balance", balance)
    return balance


lot = 0.001
sma = 50
p_num = 5

database = "tradingbot"

diffs = []
balance = 0
close_price = 0
c_num = 0
while True:
    bf_price = get_bf_price()
    li_price = get_li_price()

    diff = bf_price / li_price * 100
    diffs.append(diff)

    if len(diffs) > sma:
        diffs.pop(0)

    diff_sma = sum(diffs) / len(diffs)

    delta = diff - diff_sma
    balance = get_balance()

    if balance >= 0.001:
        close_prices = []
        for k in range(p_num):
            close_prices.append(close_price)
        order("sell", close_prices)

        if c_num > 10:
            order_cancel()
            close(balance)

        c_num += 1
    else:
        c_num = 0
        order_prices = []
        for i in range(p_num):
            ld = 0.03 * (i + 1)
            para_price = int(100 * (bf_price) / (diff_sma + ld))
            if li_price > para_price:
                order_prices.append(para_price)
        order_cancel()
        order("buy", order_prices)
        close_price = int(100 * (bf_price) / (diff_sma + 0))

    time.sleep(3)
