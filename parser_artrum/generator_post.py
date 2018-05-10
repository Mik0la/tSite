import requests
import time
import json
from pyquery import PyQuery as pq


def start():
    url = 'https://stroimedia.by/krasa-2017/'
    # url = 'http://analogi.rstc.by/'
    payloads = {'action': 'polls',
                'view': 'process',
                'poll_id': '5',
                'poll_5': '153',
                'poll_5_nonce': '9c3d716008'}

    # payloads = {'fp_h': '10'}

    headers = {'Accept': '*/*',
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'en-US,en;q=0.5',
               'Connection': 'keep-alive',
               'Content-Length': '70',
               'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
               'Host': 'stroimedia.by',
               'Referer': 'https://stroimedia.by/krasa-2017/',
               'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
               'X-Requested-With': 'XMLHttpRequest'}
    # response = requests.get(url, data=payloads, headers=headers)
    response = requests.post(url, data=payloads)
    print(response.text)
    return pq(response.content)

for i in range(1):
    r = start()
    time.sleep(1)
