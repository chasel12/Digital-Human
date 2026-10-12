import subprocess, json
from pathlib import Path
from config import VIDEOS_DIR, DOUYIN_COOKIE

url = 'https://v.douyin.com/bRkzwxU5E8U/'
out = VIDEOS_DIR / '%(id)s.%(ext)s'

# Method 1: Try with Edge browser cookies
cmd = ['yt-dlp', '--cookies-from-browser', 'edge', '-o', str(out), '--print', 'filename', url]
print('Method 1 - Edge cookies:')
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
print('  STDOUT:', result.stdout[:300])
print('  STDERR:', result.stderr[:300])
print('  RC:', result.returncode)
print()

# Method 2: Let yt-dlp try cookiesfrombrowser automatically
cmd2 = ['yt-dlp', '-o', str(out), '--print', 'filename', url]
print('Method 2 - No cookies:')
result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
print('  STDOUT:', result2.stdout[:300])
print('  STDERR:', result2.stderr[:300])
print('  RC:', result2.returncode)
print()

# Method 3: Write cookie to Netscape format and use --cookies
cookie_path = VIDEOS_DIR / 'cookies.txt'
lines = ['# Netscape HTTP Cookie File']
from config import DOUYIN_COOKIE
for item in DOUYIN_COOKIE.split(';'):
    item = item.strip()
    if '=' in item:
        k, v = item.split('=', 1)
        lines.append(f'.douyin.com\tTRUE\t/\tTRUE\t0\t{k}\t{v}')
cookie_path.write_text('\n'.join(lines), encoding='utf-8')

cmd3 = ['yt-dlp', '--cookies', str(cookie_path), '-o', str(out), '--print', 'filename', url]
print('Method 3 - Cookie file:')
result3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=60)
print('  STDOUT:', result3.stdout[:300])
print('  STDERR:', result3.stderr[:300])
print('  RC:', result3.returncode)
