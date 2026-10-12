# Try using douyin.wtf API properly
import requests, json, re

url = 'https://v.douyin.com/bRkzwxU5E8U/'
h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# resolve short URL
r = requests.head(url, headers=h, allow_redirects=True, timeout=10)
real_url = r.url
print('Real URL:', real_url)

# use douyin.wtf API
api = f'https://api.douyin.wtf/api?url={real_url}'
r2 = requests.get(api, headers=h, timeout=30)
print('douyin.wtf status:', r2.status_code)
if r2.status_code == 200:
    data = r2.json()
    video_url = data.get('nwm_video_url') or data.get('video_url')
    if video_url:
        print('Video URL:', video_url[:200])
    else:
        print('Full response:', json.dumps(data, ensure_ascii=False)[:500])
else:
    print('Response:', r2.text[:300])
