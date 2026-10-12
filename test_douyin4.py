import requests, re, json

url = 'https://v.douyin.com/bRkzwxU5E8U/'
h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
r = requests.head(url, headers=h, allow_redirects=True, timeout=10)
real_url = r.url
print('Real URL:', real_url)

aid = re.search(r'/video/(\d+)', real_url).group(1)
print('AID:', aid)

# Try public douyin parser API
apis = [
    f'https://api.douyin.wtf/api?url={real_url}',
    f'https://dy.xiaoxiangmei.com/api/douyin?url={real_url}',
]

for api_url in apis:
    try:
        r2 = requests.get(api_url, headers=h, timeout=15)
        print(f'API {api_url[:40]}: status={r2.status_code}')
        if r2.status_code == 200 and len(r2.text) > 10:
            data = r2.json()
            print('Result:', json.dumps(data, ensure_ascii=False)[:300])
    except Exception as e:
        print(f'API {api_url[:40]}: {e}')
