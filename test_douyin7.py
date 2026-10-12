import requests, re, json
from urllib.parse import quote, unquote

# Try multiple douyin API services
urls_to_try = [
    'https://v.douyin.com/bRkzwxU5E8U/',
    'https://www.douyin.com/video/7639955746892826036',
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
}

for video_url in urls_to_try:
    encoded = quote(video_url, safe='')
    
    apis = [
        ('douyin.wtf short', f'https://api.douyin.wtf/api?url={quote("https://v.douyin.com/bRkzwxU5E8U/", safe="")}'),
        ('xiaoxiangmei', f'https://dy.xiaoxiangmei.com/api/douyin?url={video_url}'),
    ]
    
    for name, api_url in apis:
        try:
            r = requests.get(api_url, headers=headers, timeout=15)
            print(f'{name}: status={r.status_code}', end='')
            if r.status_code == 200 and len(r.text) > 20:
                try:
                    data = r.json()
                    keys = list(data.keys())
                    vu = data.get('nwm_video_url') or data.get('video_url') or data.get('url')
                    if vu:
                        print(f' VIDEO URL: {vu[:150]}')
                    else:
                        print(f' keys={keys} first_100={json.dumps(data, ensure_ascii=False)[:100]}')
                except:
                    print(f' text={r.text[:80]}')
            else:
                print(f' text={r.text[:60]}')
        except Exception as e:
            print(f'{name}: FAIL {str(e)[:50]}')
