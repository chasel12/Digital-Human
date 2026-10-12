import requests, re, json
from config import DOUYIN_COOKIE

aid = '7639955746892826036'

h = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/',
    'Cookie': DOUYIN_COOKIE,
}

# try douyin web API
url = f'https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={aid}&aid=6383'
r = requests.get(url, headers=h, timeout=15)
print('Status:', r.status_code, 'Len:', len(r.text))

if r.status_code == 200 and r.text.strip():
    data = r.json()
    dd = data.get('aweme_detail') or data.get('data', {})
    if not dd:
        dd = data
    video = dd.get('video', {})
    if video:
        pa = video.get('play_addr', {})
        ul = pa.get('url_list', [])
        if ul:
            print('PLAY_ADDR:', ul[0][:200])
        else:
            # try bit_rate
            br = video.get('bit_rate', [])
            if br:
                pa2 = br[0].get('play_addr', {})
                ul2 = pa2.get('url_list', [])
                if ul2:
                    print('BITRATE:', ul2[0][:200])
            else:
                print('Video keys:', list(video.keys()))
    else:
        print('No video field, keys:', list(dd.keys())[:20])
else:
    print('Failed, response:', r.text[:300])
