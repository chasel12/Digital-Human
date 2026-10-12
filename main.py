import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from config import VIDEOS_DIR, RESULT_DIR
from modules.downloader import DouyinDownloader
from modules.asr import LocalASR
from modules.analyzer import StyleAnalyzer
from modules.script_generator import ScriptGenerator
from modules.video_generator import generate_video, list_voices

console = Console()


def step1_download() -> Path:
    console.print(Panel("[bold]Step 1: 下载抖音视频[/bold]", style="blue"))
    share_text = Prompt.ask("[cyan]请粘贴抖音分享链接或分享文本[/cyan]")
    method = Prompt.ask("[cyan]下载方式[/cyan]", choices=["ytdlp", "api"], default="ytdlp")

    downloader = DouyinDownloader()
    video_path = downloader.download(share_text, method=method)
    return video_path


def step2_asr(video_path: Path) -> str:
    console.print(Panel("[bold]Step 2: 本地 ASR 语音识别 (faster-whisper)[/bold]", style="blue"))
    transcriber = LocalASR()
    transcript = transcriber.transcribe(video_path)
    return transcript


def step3_analyze(transcript: str) -> dict:
    console.print(Panel("[bold]Step 3: 文案风格分析 (DeepSeek)[/bold]", style="blue"))
    analyzer = StyleAnalyzer()
    style = analyzer.analyze(transcript)
    return style


def step4_generate_script(style: dict, transcript: str) -> tuple[dict, list[str], list[str], str, str]:
    console.print(Panel("[bold]Step 4: 生成探店推广文案 (DeepSeek)[/bold]", style="blue"))

    product_name = Prompt.ask("[cyan]产品名称[/cyan]")
    product_description = Prompt.ask("[cyan]产品描述[/cyan]")
    store_description = Prompt.ask("[cyan]店铺描述 (可留空)[/cyan]", default="")
    product_photos_input = Prompt.ask("[cyan]产品照片路径 (逗号分隔, 可留空)[/cyan]", default="")
    store_photos_input = Prompt.ask("[cyan]店铺照片路径 (逗号分隔, 可留空)[/cyan]", default="")
    avatar_input = Prompt.ask("[cyan]数字人头像照片路径 (可留空)[/cyan]", default="")

    product_photos = [p.strip() for p in product_photos_input.split(",") if p.strip()]
    store_photos = [p.strip() for p in store_photos_input.split(",") if p.strip()]

    generator = ScriptGenerator()
    script = generator.generate(
        style_analysis=style,
        original_transcript=transcript,
        product_name=product_name,
        product_description=product_description,
        store_description=store_description,
    )

    approved = Confirm.ask("[cyan]文案是否满意?[/cyan]", default=True)
    if not approved:
        feedback = Prompt.ask("[cyan]请输入修改意见[/cyan]")
        script = generator.refine(script, feedback)

    return script, product_photos, store_photos, avatar_input


def step5_generate_video(
    script: dict,
    product_photos: list[str],
    store_photos: list[str],
    avatar_path: str,
) -> Path:
    console.print(Panel("[bold]Step 5: 生成数字人视频 (本地)[/bold]", style="blue"))

    voices = list_voices()
    voice_options = list(voices.keys())
    voice_key = Prompt.ask(
        "[cyan]选择语音风格[/cyan]",
        choices=voice_options,
        default="female_warm",
    )
    voice = voices[voice_key]

    output_path = generate_video(
        script=script,
        avatar_image=Path(avatar_path) if avatar_path else None,
        product_photos=product_photos or None,
        store_photos=store_photos or None,
        voice=voice,
    )
    return output_path


def run_full_pipeline():
    console.print(Panel(
        "[bold]数字人探店视频生成器[/bold]\n"
        "抖音视频 → faster-whisper ASR → DeepSeek风格分析 → DeepSeek文案 → edge-tts + 本地视频合成",
        style="bold magenta",
    ))

    video_path = step1_download()
    transcript = step2_asr(video_path)
    style = step3_analyze(transcript)
    script, product_photos, store_photos, avatar_path = step4_generate_script(style, transcript)
    result_path = step5_generate_video(script, product_photos, store_photos, avatar_path)

    console.print(Panel(
        f"[bold green]全部完成![/bold green]\n\n最终视频: {result_path}",
        title="成果",
        style="green",
    ))


def run_step_by_step():
    console.print(Panel(
        "[bold]数字人探店视频生成器 (分步模式)[/bold]",
        style="bold magenta",
    ))

    table = Table(title="可用步骤")
    table.add_column("编号", style="cyan")
    table.add_column("步骤", style="green")
    table.add_column("说明", style="white")
    table.add_row("1", "下载视频", "从抖音分享链接下载视频")
    table.add_row("2", "ASR识别", "faster-whisper 本地提取口播文案")
    table.add_row("3", "风格分析", "DeepSeek 分析文案风格")
    table.add_row("4", "文案生成", "DeepSeek 生成推广文案")
    table.add_row("5", "视频生成", "edge-tts + moviepy 合成视频")
    table.add_row("0", "全部执行", "依次执行所有步骤")
    console.print(table)

    step = Prompt.ask("[cyan]请选择步骤[/cyan]", choices=["0", "1", "2", "3", "4", "5"])

    if step == "0":
        run_full_pipeline()
        return

    if step == "1":
        step1_download()

    elif step == "2":
        video_input = Prompt.ask("[cyan]视频文件路径 (或抖音链接)[/cyan]")
        if video_input.startswith("http") or "douyin" in video_input:
            downloader = DouyinDownloader()
            video_path = downloader.download(video_input)
        else:
            video_path = Path(video_input)
        step2_asr(video_path)

    elif step == "3":
        transcript_input = Prompt.ask("[cyan]口播文案 (直接输入或文件路径)[/cyan]")
        if Path(transcript_input).exists():
            transcript = Path(transcript_input).read_text(encoding="utf-8")
        else:
            transcript = transcript_input
        step3_analyze(transcript)

    elif step == "4":
        transcript_input = Prompt.ask("[cyan]原始口播文案 (直接输入或文件路径)[/cyan]")
        if Path(transcript_input).exists():
            transcript = Path(transcript_input).read_text(encoding="utf-8")
        else:
            transcript = transcript_input

        style_input = Prompt.ask("[cyan]风格分析JSON (文件路径, 可留空自动分析)[/cyan]", default="")
        if style_input and Path(style_input).exists():
            style = json.loads(Path(style_input).read_text(encoding="utf-8"))
        elif style_input:
            style = json.loads(style_input)
        else:
            analyzer = StyleAnalyzer()
            style = analyzer.analyze(transcript)

        step4_generate_script(style, transcript)

    elif step == "5":
        script_input = Prompt.ask("[cyan]文案JSON文件路径[/cyan]")
        if Path(script_input).exists():
            with open(script_input, "r", encoding="utf-8") as f:
                script = json.load(f)
        else:
            script = json.loads(script_input)

        product_photos_input = Prompt.ask("[cyan]产品照片路径 (逗号分隔)[/cyan]", default="")
        store_photos_input = Prompt.ask("[cyan]店铺照片路径 (逗号分隔)[/cyan]", default="")
        avatar_input = Prompt.ask("[cyan]数字人头像照片路径[/cyan]", default="")

        product_photos = [p.strip() for p in product_photos_input.split(",") if p.strip()]
        store_photos = [p.strip() for p in store_photos_input.split(",") if p.strip()]

        step5_generate_video(script, product_photos, store_photos, avatar_input)


if __name__ == "__main__":
    mode = Prompt.ask(
        "[cyan]运行模式[/cyan]",
        choices=["full", "step"],
        default="full",
    )

    if mode == "full":
        run_full_pipeline()
    else:
        run_step_by_step()
