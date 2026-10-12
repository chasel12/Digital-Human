import yt_dlp

url = 'https://v.douyin.com/bRkzwxU5E8U/'

# Try with cookiesfrombrowser=chrome
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'cookiesfrombrowser': ('chrome',),
    'extractor_retries': 3,
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print('Title:', info.get('title', ''))
        print('Duration:', info.get('duration', ''))
        # list formats
        formats = info.get('formats', [])
        for f in formats:
            if f.get('vcodec') != 'none':
                print('Format:', f.get('format_id'), f.get('ext'), f.get('filesize', ''))
        # get best video URL
        fl = info.get('url', '')
        if not fl:
            fl = formats[0].get('url', '') if formats else ''
        print('Video URL:', fl[:200] if fl else 'N/A')
except Exception as e:
    print('FAIL:', str(e)[:300])
