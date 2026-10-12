"Extract Douyin video URL by intercepting API"
import json, re, sys
from playwright.sync_api import sync_playwright
from config import DOUYIN_COOKIE

def main():
    cookies = {}
    for item in DOUYIN_COOKIE.split(';'):
        if '=' in item:
            k, v = item.split('=', 1)
            cookies[k.strip()] = v.strip()

    video_url = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        context.add_cookies([
            {'name': k, 'value': v, 'domain': '.douyin.com', 'path': '/'}
            for k, v in cookies.items()
        ])

        page = context.new_page()

        # Intercept API responses
        def handle_response(response):
            nonlocal video_url
            url = response.url
            if '/aweme/v1/web/aweme/detail/' in url or '/aweme/v1/web/aweme/post/' in url or '/v1/web/' in url:
                try:
                    data = response.json()
                    detail = data.get('aweme_detail') or data.get('data', {}).get('aweme_detail') or {}
                    video_data = detail.get('video', {})
                    play_addr = video_data.get('play_addr', {})
                    url_list = play_addr.get('url_list', [])
                    if url_list:
                        video_url = url_list[-1]
                        print(f'Found video URL from API: {video_url[:100]}...', flush=True)
                except Exception:
                    pass

        page.on('response', handle_response)

        page.goto('https://www.douyin.com/video/7639955746892826036', wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(5000)

        # Also try to extract from page JS
        if not video_url:
            try:
                video_url = page.evaluate('''() => {
                    try {
                        return document.querySelector('video')?.src || null;
                    } catch(e) { return null; }
                }''')
                if video_url:
                    print(f'Found video URL from video tag: {video_url[:100]}...', flush=True)
            except Exception as e:
                print(f'video tag eval failed: {e}', flush=True)

        if not video_url:
            # Try accessing window data
            try:
                url_from_js = page.evaluate('''() => {
                    try {
                        const el = document.querySelector('[class*="video"] video');
                        return el ? el.src : null;
                    } catch(e) { return null; }
                }''')
                if url_from_js:
                    video_url = url_from_js
                    print(f'Found video URL from class search: {video_url[:100]}...', flush=True)
            except Exception as e:
                print(f'class search eval failed: {e}', flush=True)

        browser.close()

    if video_url:
        print(f'\nVIDEO_URL={video_url}', flush=True)
    else:
        print('NO VIDEO URL FOUND', flush=True)

if __name__ == '__main__':
    main()
