import subprocess
from pathlib import Path
from config import VIDEOS_DIR

url = 'https://v.douyin.com/bRkzwxU5E8U/'
out = VIDEOS_DIR / '%(id)s.%(ext)s'

# Try with --no-optimized-cookies workaround
methods = [
    ['yt-dlp', '--cookies-from-browser', 'chrome:~', '-o', str(out), url],
    ['yt-dlp', '--cookies-from-browser', 'edge:~', '-o', str(out), url],
    ['yt-dlp', '--cookies-from-browser', 'firefox:default', '-o', str(out), url],
    ['yt-dlp', '--no-cache-dir', '--extractor-retries', '5', '-o', str(out), url],
]

for i, cmd in enumerate(methods):
    print(f'Method {i+1}: {cmd[1]} {cmd[2] if len(cmd)>2 else ""}')
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    out_text = result.stdout.strip()
    err_text = result.stderr.strip()
    if 'download' in out_text.lower() or '.mp4' in out_text.lower() or '.webm' in out_text.lower():
        print(f'  SUCCESS: {out_text[:200]}')
        break
    err_short = err_text[:200] if err_text else 'no error'
    print(f'  FAIL: {err_short}')
    print()
