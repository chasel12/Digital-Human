"Download Douyin video using extracted URL"
import requests
from config import DOUYIN_COOKIE, VIDEOS_DIR

VIDEO_URL = "https://www.douyin.com/aweme/v1/play/?video_id=v2700fgi0000d83968fog65ovkpvm36g&line=0&file_id=b1172119a0e34bb2bd9a77f3db4ff602&sign=205e9fee4c7d60f106e2e9ecc297033d&is_play_url=1&source=PackSourceEnum_AWEME_DETAIL"

cookies = {}
for item in DOUYIN_COOKIE.split(';'):
    if '=' in item:
        k, v = item.split('=', 1)
        cookies[k.strip()] = v.strip()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/',
    'Accept': '*/*',
    'Range': 'bytes=0-',
}

r = requests.get(VIDEO_URL, headers=headers, cookies=cookies, stream=True, timeout=30)
print(f'Status: {r.status_code}')
print(f'Headers: {dict(r.headers)}')
print(f'Content-Length: {r.headers.get("Content-Length", "unknown")}')
print(f'Content-Type: {r.headers.get("Content-Type", "unknown")}')

if r.status_code == 200 or r.status_code == 206:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    out = VIDEOS_DIR / 'test_douyin_download.mp4'
    downloaded = 0
    with open(out, 'wb') as f:
        for chunk in r.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
    print(f'Downloaded: {downloaded} bytes to {out}')
elif r.status_code == 302 or r.status_code == 301:
    print(f'Redirect to: {r.headers.get("Location", "none")}')
    r2 = requests.get(r.headers['Location'], headers=headers, stream=True, timeout=30)
    print(f'Redirect status: {r2.status_code}')
else:
    print(f'Response body: {r.text[:200]}')
