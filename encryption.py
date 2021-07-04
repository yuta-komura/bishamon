import hashlib
import hmac
import json

import requests
import urllib3


def create(apiKey, secretKey):
    params = {
        "symbol": "BTCUSD",
        "api_key": apiKey
    }
    sign = ''
    for key in sorted(params.keys()):
        v = params[key]
        if isinstance(params[key], bool):
            if params[key]:
                v = 'true'
            else:
                v = 'false'
        sign += key + '=' + v + '&'
    sign = sign[:-1]
    hash = hmac.new(secretKey, sign.encode("utf-8"), hashlib.sha256)
    signature = hash.hexdigest()
    sign_real = {
        "sign": signature
    }
    url = 'https://api.bybit.com/v2/public/orderBook/L2'
    headers = {"Content-Type": "application/json"}
    body = dict(params, **sign_real)
    urllib3.disable_warnings()
    s = requests.session()
    s.keep_alive = False
    response = requests.get(
        url,
        data=json.dumps(body),
        headers=headers,
        verify=False)
    print(response)
    print(response.text)


def main():
    apiKey = "50mOY6I7XRkQth9dLv"
    secret = b"6d30dJ80nVHA8FWtBqFJs2Ut8tZn6aQbByij"
    create(apiKey, secret)


if __name__ == '__main__':
    main()
