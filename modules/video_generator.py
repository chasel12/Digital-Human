import asyncio
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from config import RESULT_DIR

console = Console()

ZH_VOICES = {
    "female_warm": "zh-CN-XiaoxiaoNeural",
    "female_lively": "zh-CN-XiaoyiNeural",
    "male_passion": "zh-CN-YunjianNeural",
    "male_lively": "zh-CN-YunxiNeural",
    "male_pro": "zh-CN-YunyangNeural",
    "male_cute": "zh-CN-YunxiaNeural",
}


def list_voices() -> dict:
    return ZH_VOICES


async def _tts(text: str, output_path: Path, voice: str = "zh-CN-XiaoxiaoNeural"):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


async def generate_video(
    script: dict,
    avatar_image: Path | None = None,
    product_photos: list[str | Path] | None = None,
    store_photos: list[str | Path] | None = None,
    voice: str = "zh-CN-XiaoxiaoNeural",
    output_path: Path | None = None,
) -> Path:
    from moviepy import (
        ImageClip, AudioFileClip, CompositeVideoClip,
        TextClip, ColorClip, concatenate_videoclips,
    )

    if output_path is None:
        output_path = RESULT_DIR / "result.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scenes = script.get("scenes", [])
    if not scenes:
        script_text = script.get("script", script.get("raw_script", ""))
        if isinstance(script_text, list):
            script_text = "\n".join(script_text)
        scenes = [{"scene_type": "digital_human", "text": script_text, "duration": 10}]

    W, H = 1080, 1920

    console.print(f"[cyan]正在生成 {len(scenes)} 个场景的视频...[/cyan]")

    all_audio_paths = []
    video_clips = []

    avatar_dir = Path(__file__).parent.parent / "assets"
    if avatar_image is None:
        default_avatar = avatar_dir / "default_avatar.png"
        if default_avatar.exists():
            avatar_image = default_avatar

    product_images = [Path(p) for p in (product_photos or [])]
    store_images = [Path(p) for p in (store_photos or [])]
    product_idx = 0
    store_idx = 0

    for i, scene in enumerate(scenes):
        scene_type = scene.get("scene_type", "digital_human")
        text = scene.get("text", "")
        duration = scene.get("duration", 5)

        audio_path = RESULT_DIR / f"tts_scene_{i}.mp3"
        audio_clip = None

        if text.strip():
            console.print(f"[dim]  场景{i+1}/{len(scenes)}: TTS ({len(text)}字)...[/dim]")
            await _tts(text, audio_path, voice)
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            all_audio_paths.append(audio_path)
            audio_clip = AudioFileClip(str(audio_path))
            duration = max(duration, audio_clip.duration + 0.5)

        bg_clip = None

        if scene_type == "digital_human" and avatar_image and avatar_image.exists():
            from PIL import Image
            img = Image.open(avatar_image).convert("RGB")
            img = img.resize((W, H))
            frame_path = RESULT_DIR / f"avatar_frame_{i}.png"
            img.save(str(frame_path))
            bg_clip = ImageClip(str(frame_path), duration=duration)

        elif scene_type == "product" and product_idx < len(product_images):
            from PIL import Image
            pimg = product_images[product_idx]
            if pimg.exists():
                img = Image.open(pimg).convert("RGB")
                img = img.resize((W, H))
                frame_path = RESULT_DIR / f"product_frame_{i}.png"
                img.save(str(frame_path))
                bg_clip = ImageClip(str(frame_path), duration=duration)
            product_idx += 1

        elif scene_type == "store" and store_idx < len(store_images):
            from PIL import Image
            simg = store_images[store_idx]
            if simg.exists():
                img = Image.open(simg).convert("RGB")
                img = img.resize((W, H))
                frame_path = RESULT_DIR / f"store_frame_{i}.png"
                img.save(str(frame_path))
                bg_clip = ImageClip(str(frame_path), duration=duration)
            store_idx += 1

        if bg_clip is None:
            bg_clip = ColorClip(size=(W, H), color=(30, 30, 50), duration=duration)

        if audio_clip is not None:
            bg_clip = bg_clip.with_audio(audio_clip.subclipped(0, min(audio_clip.duration, duration)))

        video_clips.append(bg_clip)

    if not video_clips:
        raise ValueError("没有可生成的场景")

    console.print("[cyan]正在合并视频片段...[/cyan]")
    final = concatenate_videoclips(video_clips)

    console.print("[cyan]正在写入最终视频 (这可能需要几分钟)...[/cyan]")
    final.write_videofile(
        str(output_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )

    for p in all_audio_paths:
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass

    console.print(f"[green][OK] 视频已保存: {output_path}[/green]")
    console.print(Panel(str(output_path), title="最终视频", style="green"))
    return output_path
