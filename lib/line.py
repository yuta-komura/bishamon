
import requests

from lib.config import Line


def notify(message):
    token = Line.TOKEN.value
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {token}'}
    data = {'message': f'{message}'}
    requests.post(url, headers=headers, data=data)
