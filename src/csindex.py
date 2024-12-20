from datetime import datetime

import requests

"""
中证官网下载
"""


def download_file(code, start_date):
    print('request %s' % code)
    url = 'https://www.csindex.com.cn/csindex-home/exportExcel/downloadindex-perf?language=CH'
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        'Cookie': 'Hm_lvt_f0fbc9a7e7e7f29a55a0c13718e9e542=1732775805; ssxmod_itna=QqRxnDcDR70==D5G=G0D2iKIxiQ07KbKKDzxC5iOCDuxiK08D6ADBb=DQ6mF=q3NYGCu06xFYhAx21DBu44bDnqD82DQeDvYPuG01b8CqhPQtVrBYKPyCzTAT4LObD2DIjOLtXMkmKi4GLDY=DCu5bGGeD44dDt4DIDAYDDxDW04DLDYoDYbTPxGpoujuNvjrWD0YDzqDglDpTxG3D08bdmi+kIeGEDA3DG3bDmRRkDDXkW/KPj03qDYpogW0Fr2qDAkDtokbDjkPD/4h0yPDBevlkepu6oq8I8CcaxBQD7dF=onq8jmWNaenYxq74qYrsWi+iGTQ4etire2DxTNQDNjG49x4UhPebNQRxorq9xYxKomi+3heYrPaElf5/Im/B5+4oTKwT3B1in7miuS+YrGet0tlAPCTKKibWYxYGY8G4F0xPD; ssxmod_itna2=QqRxnDcDR70==D5G=G0D2iKIxiQ07KbKKDzxC5iOCDuxiK08D6ADBb=DQ6mF=q3NYGCu06xFYhAxrbDG+m44bYDrqowyDj+PjipbcDD/mG=39xYDwxkw2/D5kk4uqzNIGg02KG=LPyu9uNlzuYjmTwyY+LMKGtBQGjgzTxjGuQnR4Uj/qbBGiROfCmx5dKEmWhZ+O4okAbe7QjQNuQdDqF3u4+rKBIk8D=Ty+5eQT+yjDRzfaQ63Kr3cTddttIt67u0mYuvEq++Pjr0K7QdAe2h1/KmXTh6eHNHOqWYC=gyL9D3pB1ku+rSmoYohKDIAOhU=U3Pd0YioaQToEbh0x6PBD0yB3NxfMC2xO63OtiO2uENm6vNhxq7L7GGjAG9m5oioPjo5=GNp06n5PDhyD2NaGQUPQKq4nUugA=0pyp5Yr=ooYA3Uv9W4EPk/IMeW5puNUTjGD5P6v6tiU3iP6bzcj=Ei3oCFf6=KKjGkDxur5Plw0S3C4IEWoK0Psr+Srezmf1mPG1velEqsweT5djpKkAGjKs+6dZE6ct4emnlUQVgEa+MfeoqhAni47L3MLrHTHsIrsqei4oi+k0kmYpb0wKh=FyAmDh1AMvjlkYD'
    }
    today = datetime.now().strftime('%Y%m%d')
    json_data = [{
        'indexCode': code,
        'startDate': start_date,
        'endDate': today,
    }]
    response = requests.post(url, json=json_data, headers=headers)
    print('saving %s' % code)
    if response.status_code == 200:
        with open(f'../data/download_{code}.xlsx', 'wb', ) as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)


download_file("000300", '20130101')
download_file("000510", '20130101')
download_file("000852", '20130101')
download_file("000905", '20130101')
download_file("H20269", '20130101')
download_file("H20955", '20130101')
download_file("000922CNY020", '20130101')
