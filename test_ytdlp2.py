import subprocess, json
from pathlib import Path
from config import VIDEOS_DIR

url = 'https://v.douyin.com/bRkzwxU5E8U/'
out = VIDEOS_DIR / '%(id)s.%(ext)s'

# try yt-dlp via CLI with --cookies-from-browser chrome
cmd = [
    'yt-dlp',
    '--cookies-from-browser', 'chrome',
    '-o', str(out),
    '--print', 'filename',
    url,
]

print('Running:', ' '.join(cmd))
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
print('STDOUT:', result.stdout[:500])
print('STDERR:', result.stderr[:500])
print('RC:', result.returncode)
