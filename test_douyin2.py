import requests, re, json
from urllib.parse import unquote

aid = '7639955746892826036'

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
    'Referer': 'https://www.douyin.com/',
}
r = requests.get(f'https://www.iesdouyin.com/share/video/{aid}', headers=headers, timeout=15)
print('Status:', r.status_code, 'Len:', len(r.text))

# show all script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
print('Script tags:', len(scripts))
for i, s in enumerate(scripts):
    s = s.strip()
    if len(s) > 100 and ('video' in s or 'play' in s or 'mp4' in s):
        print(f'Script {i}: len={len(s)}, preview={s[:200]}')
        break

# search playAddr in JSON
for m in re.finditer(r'\{[^{}]*"play_addr"[^{}]*\}', r.text):
    print('Found play_addr block:', m.group()[:300])
    break

# search mp4-like URLs
urls = re.findall(r'https://[^\x22\x27\s<>]+', r.text)
for u in urls:
    lu = u.lower()
    if ('douyinvod' in lu or 'douyin' in lu) and ('play' in lu or 'mp4' in lu or 'video' in lu):
        print('FOUND:', u[:200])
