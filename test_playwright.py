"Test Douyin with Playwright"
import json, re
from playwright.sync_api import sync_playwright
from config import DOUYIN_COOKIE

def main():
    cookies = {}
    for item in DOUYIN_COOKIE.split(';'):
        if '=' in item:
            k, v = item.split('=', 1)
            cookies[k.strip()] = v.strip()

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
        page.goto('https://www.douyin.com/video/7639955746892826036', wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(3000)
        html = page.content()
        print(f'Page loaded, len={len(html)}')
        print(f'Has INITIAL_STATE: {"__INITIAL_STATE__" in html}')
        print(f'Title: {page.title().encode("ascii", "ignore").decode()}')
        print(f'URL: {page.url}')

        if '__INITIAL_STATE__' in html:
            m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
            if m:
                state = json.loads(m.group(1))
                print(json.dumps(state, ensure_ascii=False)[:800])
        else:
            print('Page body text (first 500):')
            text = page.inner_text('body')[:500] if page.query_selector('body') else ''
            print(text.encode('ascii', 'ignore').decode()[:500])

        page.screenshot(path='douyin_debug.png')
        print('Screenshot saved')

        browser.close()

if __name__ == '__main__':
    main()
