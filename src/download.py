import datetime
import json

import requests

"""
中证官网下载
"""
def download_file(code, duration=10):
    print('request %s', code)
    url = 'https://www.csindex.com.cn/csindex-home/exportExcel/downloadindex-perf?language=CH&type__1773=n40xcDyD0DRDuDjOxBT%3Dx2G7GC9y6hb7qID'
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
    }
    now = datetime.datetime.now()
    json_data = [{
        'endDate': now.strftime('%Y%m%d'),
        'indexCode': code,
        'startDate': now.replace(year=now.year-duration).strftime('%Y%m%d'),
    }]
    response = requests.post(url, json=json_data, headers=headers)
    print('saving %s', code)
    if response.status_code == 200:
        with open(f'../data/download_{code}.xlsx', 'wb',) as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)


# download_file("000510", 12)
# download_file("H20955", 12)
download_file("000300", 12)
download_file("H20269", 12)
