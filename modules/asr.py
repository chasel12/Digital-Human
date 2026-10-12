import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

console = Console()


class LocalASR:
    def __init__(self, model_size: str | None = None):
        from config import WHISPER_MODEL_SIZE
        self.model_size = model_size or WHISPER_MODEL_SIZE
        self.model = None

    def _load_model(self):
        if self.model is not None:
            return
        from faster_whisper import WhisperModel
        console.print(f"[cyan]正在加载 Whisper 模型 ({self.model_size}, 首次需下载)...[/cyan]")
        self.model = WhisperModel(
            self.model_size,
            device="cpu",
            compute_type="int8",
        )
        console.print("[green][OK] 模型加载完成[/green]")

    def extract_audio(self, video_path: Path) -> Path:
        import av

        audio_path = video_path.with_suffix(".wav")
        console.print("[cyan]正在从视频中提取音频 (PyAV)...[/cyan]")

        input_container = av.open(str(video_path))
        audio_stream = next((s for s in input_container.streams if s.type == "audio"), None)

        if audio_stream is None:
            raise ValueError("视频中没有音频轨道")

        output_container = av.open(str(audio_path), mode="w")
        output_stream = output_container.add_stream("pcm_s16le", rate=16000, layout="mono")

        resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)

        for frame in input_container.decode(audio_stream):
            resampled = resampler.resample(frame)
            for r in resampled:
                for packet in output_stream.encode(r):
                    output_container.mux(packet)

        for packet in output_stream.encode():
            output_container.mux(packet)

        output_container.close()
        input_container.close()

        console.print(f"[green][OK] 音频已提取: {audio_path.name}[/green]")
        return audio_path

    def transcribe(self, video_path: Path) -> str:
        self._load_model()

        audio_path = self.extract_audio(video_path)

        console.print("[cyan]正在通过 faster-whisper 识别语音 (中文)...[/cyan]")
        segments, info = self.model.transcribe(
            str(audio_path),
            language="zh",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200,
            ),
        )

        console.print(f"[dim]检测到语言: {info.language} (概率: {info.language_probability:.2f})[/dim]")

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        full_text = "".join(text_parts)

        console.print("[green][OK] 语音识别完成[/green]")
        console.print(Panel(full_text, title="口播文案", style="green"))
        return full_text
