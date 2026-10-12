import requests, re, json
from urllib.parse import unquote

aid = '7639955746892826036'
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
}
r = requests.get(f'https://www.iesdouyin.com/share/video/{aid}', headers=headers, timeout=15)
text = r.text

# Save HTML to inspect
with open('output/page.html', 'w', encoding='utf-8') as f:
    f.write(text)

# Find ALL external references (images, videos)
sources = re.findall(r'https://[^\s"\'<>]+', text)
for s in sources:
    sl = s.lower()
    if any(x in sl for x in ['.mp4', '.m3u8', 'play', 'video/id', 'video/urls', 'aweme', 'douyinvod']):
        print(s[:200])

# Search for any JSON data
import html
text_decoded = html.unescape(text)
potential_json = re.findall(r'\{[^{}]*"video"[^{}]*\}', text_decoded)
for j in potential_json[:5]:
    try:
        d = json.loads(j)
        if isinstance(d, dict) and 'play_addr' in json.dumps(d, ensure_ascii=False):
            print('JSON block:', j[:300])
    except:
        pass
