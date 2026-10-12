from curl_cffi import requests as curl_requests
import json

# Try douyin.wtf API with curl_cffi (bypasses Cloudflare)
video_url = 'https://v.douyin.com/bRkzwxU5E8U/'
api_url = f'https://api.douyin.wtf/api?url={video_url}'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
}

try:
    r = curl_requests.get(api_url, headers=headers, impersonate='chrome124', timeout=30)
    print('Status:', r.status_code)
    print('Text length:', len(r.text))
    if r.status_code == 200:
        data = r.json()
        vu = data.get('nwm_video_url') or data.get('video_url') or data.get('url')
        if vu:
            print('VIDEO URL:', vu[:200])
        else:
            print('Response keys:', list(data.keys()))
            print('Preview:', json.dumps(data, ensure_ascii=False)[:300])
    else:
        print('Response:', r.text[:300])
except Exception as e:
    print('Error:', e)
