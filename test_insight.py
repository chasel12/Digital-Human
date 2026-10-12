from douyin_insight import DouyinInsight
from config import DOUYIN_COOKIE

di = DouyinInsight()
url = 'https://v.douyin.com/bRkzwxU5E8U/'

# Method 1: yt-dlp via douyin-insight
try:
    info = di.download(url, output_dir='output/videos')
    print('Success:', info)
except Exception as e:
    print('Error:', str(e)[:500])
