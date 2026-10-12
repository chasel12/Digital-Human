import requests, re, json, hmac, hashlib, time, urllib.parse

aid = '7639955746892826036'

# Mobile web API - less protection
s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
})

# Step 1: visit the share page to get cookies
share_url = f'https://www.iesdouyin.com/share/video/{aid}'
r = s.get(share_url, timeout=15)
print('Mobile page status:', r.status_code, 'len:', len(r.text))

# extract any video URL from the page
play_urls = re.findall(r'https://[^"\'<>]+play[^"\'<>]+', r.text)
for u in play_urls:
    print('  play URL:', u[:200])

# try to find the video data
for m in re.finditer(r'video[^}]*play_addr[^}]*url_list[^}]*"([^"]+)"', r.text):
    print('  Found in page:', m.group(1)[:200])

# Step 2: use the watermark removal service
for service_url in [
    f'https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={aid}',
]:
    r2 = s.get(service_url, timeout=15)
    print(f'Web API status: {r2.status_code} len: {len(r2.text)}')
    if len(r2.text) > 10:
        print('  Response:', r2.text[:300])
