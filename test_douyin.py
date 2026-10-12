"Test Douyin download with curl_cffi"
from curl_cffi import requests as curl_requests
from config import DOUYIN_COOKIE

cookies = {}
for item in DOUYIN_COOKIE.split(';'):
    if '=' in item:
        k, v = item.split('=', 1)
        cookies[k.strip()] = v.strip()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/',
}

for v in ['chrome124', 'chrome120', 'chrome116', 'chrome110', 'chrome107', 'chrome104', 'chrome101']:
    try:
        url = 'https://www.douyin.com/video/7639955746892826036'
        r = curl_requests.get(url, headers=headers, cookies=cookies, impersonate=v, timeout=20)
        has = '__INITIAL_STATE__' in r.text
        c = 'captcha' in r.text.lower() or 'verify' in r.text.lower()
        print(f'{v}: status={r.status_code} len={len(r.text)} has_state={has} captcha={c}')
        if has:
            print('  SUCCESS!')
            break
    except Exception as e:
        print(f'{v}: {type(e).__name__}: {e}')
