import json
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import RESULT_DIR, VIDEOS_DIR, BASE_DIR, DOUYIN_COOKIE
from modules.downloader import DouyinDownloader
from modules.asr import LocalASR
from modules.analyzer import StyleAnalyzer
from modules.script_generator import ScriptGenerator
from modules.video_generator import generate_video, list_voices

app = FastAPI(title="数字人探店视频生成器")

asr_engine = None
analyzer = StyleAnalyzer()
script_gen = ScriptGenerator()
downloader = DouyinDownloader(cookie_str=DOUYIN_COOKIE)


def get_asr():
    global asr_engine
    if asr_engine is None:
        asr_engine = LocalASR()
    return asr_engine


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = BASE_DIR / "frontend" / "index.html"
    return html_path.read_text(encoding="utf-8")


@app.post("/api/download")
async def api_download(douyin_url: str = Form(...)):
    try:
        video_path = downloader.download(douyin_url.strip())
        return {"ok": True, "video_path": str(video_path), "name": video_path.name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/upload_video")
async def api_upload_video(video: UploadFile = File(...)):
    try:
        ext = Path(video.filename).suffix if video.filename else ".mp4"
        video_name = f"upload_{uuid.uuid4().hex[:8]}{ext}"
        video_path = VIDEOS_DIR / video_name
        video_path.parent.mkdir(parents=True, exist_ok=True)
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video.file, f)
        return {"ok": True, "video_path": str(video_path), "name": video_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/asr")
async def api_asr(video_path: str = Form(...)):
    try:
        engine = get_asr()
        transcript = engine.transcribe(Path(video_path))
        return {"ok": True, "transcript": transcript}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/analyze")
async def api_analyze(transcript: str = Form(...)):
    try:
        style = analyzer.analyze(transcript)
        return {"ok": True, "style": style}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/generate_script")
async def api_generate_script(
    transcript: str = Form(...),
    style_json: str = Form("{}"),
    product_name: str = Form(...),
    product_desc: str = Form(""),
    store_desc: str = Form(""),
    duration: int = Form(60),
):
    try:
        style = json.loads(style_json) if style_json.strip() else {}
        script = script_gen.generate(
            style_analysis=style,
            original_transcript=transcript,
            product_name=product_name,
            product_description=product_desc,
            store_description=store_desc,
            target_duration=duration,
        )
        return {"ok": True, "script": script}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/refine_script")
async def api_refine_script(script_json: str = Form(...), feedback: str = Form(...)):
    try:
        script = json.loads(script_json)
        refined = script_gen.refine(script, feedback)
        return {"ok": True, "script": refined}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/generate_video")
async def api_generate_video(
    script_json: str = Form(...),
    voice_key: str = Form("female_warm"),
    avatar: UploadFile = File(None),
    product_images: list[UploadFile] = File(default_factory=list),
    store_images: list[UploadFile] = File(default_factory=list),
):
    try:
        script = json.loads(script_json)
        voices = list_voices()
        voice = voices.get(voice_key, "zh-CN-XiaoxiaoNeural")

        upload_dir = RESULT_DIR / f"upload_{uuid.uuid4().hex[:8]}"
        upload_dir.mkdir(parents=True, exist_ok=True)

        avatar_path = None
        if avatar:
            p = upload_dir / f"avatar_{avatar.filename}"
            with open(p, "wb") as f:
                shutil.copyfileobj(avatar.file, f)
            avatar_path = p

        product_paths = []
        for img in product_images:
            p = upload_dir / f"product_{img.filename}"
            with open(p, "wb") as f:
                shutil.copyfileobj(img.file, f)
            product_paths.append(p)

        store_paths = []
        for img in store_images:
            p = upload_dir / f"store_{img.filename}"
            with open(p, "wb") as f:
                shutil.copyfileobj(img.file, f)
            store_paths.append(p)

        output_name = f"result_{uuid.uuid4().hex[:8]}.mp4"
        output_path = RESULT_DIR / output_name

        result = await generate_video(
            script=script,
            avatar_image=avatar_path,
            product_photos=product_paths or None,
            store_photos=store_paths or None,
            voice=voice,
            output_path=output_path,
        )
        return {"ok": True, "video_path": str(result), "video_name": output_name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/voices")
async def api_voices():
    return list_voices()


@app.get("/api/video/{video_name}")
async def api_get_video(video_name: str):
    for d in [RESULT_DIR, VIDEOS_DIR]:
        p = d / video_name
        if p.exists():
            return FileResponse(str(p), media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Video not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=False)
