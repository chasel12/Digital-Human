import re
import json
import requests
from pathlib import Path

import config


class DouyinDownloader:
    def __init__(self, cookie_str: str = ""):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Referer": "https://www.douyin.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.cookie_str = cookie_str
        self._cookie_jar = self._parse_cookies(cookie_str) if cookie_str else {}

    def _parse_cookies(self, s: str) -> dict:
        jar = {}
        for item in s.split(";"):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                jar[k.strip()] = v.strip()
        return jar

    def extract_url_from_share_text(self, share_text: str) -> str:
        m = re.search(r'https?://[^\s]+', share_text)
        return m.group() if m else share_text

    def resolve_short_url(self, url: str) -> str:
        try:
            r = requests.get(
                url,
                headers={**self.headers, "Accept": "application/json, text/plain, */*"},
                allow_redirects=True,
                timeout=15,
            )
            return str(r.url)
        except Exception:
            return url

    def _extract_aweme_id(self, url: str) -> str | None:
        patterns = [r'/video/(\d+)', r'/note/(\d+)', r'modal_id=(\d+)', r'/(\d{15,})']
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return None

    def download_via_playwright(self, url: str) -> Path:
        """Use Playwright to load the page and intercept the video API response."""
        aweme_id = self._extract_aweme_id(url)
        if not aweme_id:
            raise ValueError(f"无法从URL提取视频ID: {url}")

        from playwright.sync_api import sync_playwright

        video_url = None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=self.headers["User-Agent"],
                viewport={"width": 1920, "height": 1080},
            )
            ctx.add_cookies([
                {"name": k, "value": v, "domain": ".douyin.com", "path": "/"}
                for k, v in self._cookie_jar.items()
            ])

            page = ctx.new_page()

            def on_response(resp):
                nonlocal video_url
                if video_url:
                    return
                if "/aweme/v1/web/aweme/detail/" in resp.url:
                    try:
                        data = resp.json()
                        detail = data.get("aweme_detail", {})
                        play_addr = detail.get("video", {}).get("play_addr", {})
                        url_list = play_addr.get("url_list", [])
                        if url_list:
                            video_url = url_list[-1]
                    except Exception:
                        pass

            page.on("response", on_response)

            page.goto(f"https://www.douyin.com/video/{aweme_id}",
                      wait_until="domcontentloaded", timeout=25_000)
            page.wait_for_timeout(3000)
            browser.close()

        if not video_url:
            raise ValueError("Playwright未能获取到视频链接，cookie可能已过期")

        return self._download_file(video_url, aweme_id)

    def _download_file(self, video_url: str, aweme_id: str) -> Path:
        config.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        out = config.VIDEOS_DIR / f"douyin_{aweme_id}.mp4"

        r = requests.get(
            video_url,
            headers={**self.headers, "Accept": "*/*", "Range": "bytes=0-"},
            cookies=self._cookie_jar,
            stream=True,
            timeout=120,
        )
        r.raise_for_status()

        with open(out, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)

        return out

    def download(self, share_text: str) -> Path:
        url = self.extract_url_from_share_text(share_text)
        real_url = self.resolve_short_url(url)
        aweme_id = self._extract_aweme_id(real_url)

        errors = []

        # Method 1: Playwright (most reliable)
        try:
            return self.download_via_playwright(real_url)
        except Exception as e:
            errors.append(f"Playwright: {e}")

        # Method 2: yt-dlp (fallback)
        try:
            return self._download_via_ytdlp(real_url)
        except Exception as e:
            errors.append(f"yt-dlp: {e}")

        raise ValueError(
            f"所有下载方式均失败:\n"
            + "\n".join(errors)
            + "\n\n建议: 手动下载视频后使用 上传视频 功能"
        )

    def _download_via_ytdlp(self, url: str) -> Path:
        import yt_dlp
        config.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

        ydl_opts = {
            "outtmpl": str(config.VIDEOS_DIR / "%(id)s.%(ext)s"),
            "format": "best",
            "quiet": True,
            "no_warnings": True,
            "extractor_retries": 2,
            "http_headers": self.headers,
        }

        for browser in ["firefox", "chrome", "edge"]:
            try:
                test = yt_dlp.YoutubeDL({**ydl_opts, "cookiesfrombrowser": (browser,), "listformats": None})
                test.close()
                ydl_opts["cookiesfrombrowser"] = (browser,)
                break
            except Exception:
                continue
        else:
            if self.cookie_str:
                cookie_path = config.VIDEOS_DIR / "cookies.txt"
                lines = ["# Netscape HTTP Cookie File"]
                for k, v in self._cookie_jar.items():
                    lines.append(f".douyin.com\tTRUE\t/\tTRUE\t0\t{k}\t{v}")
                cookie_path.parent.mkdir(parents=True, exist_ok=True)
                cookie_path.write_text("\n".join(lines), encoding="utf-8")
                ydl_opts["cookiefile"] = str(cookie_path)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return Path(ydl.prepare_filename(info))
