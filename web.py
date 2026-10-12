import gradio as gr
import json
import uuid
from pathlib import Path

from config import RESULT_DIR, VIDEOS_DIR
from modules.downloader import DouyinDownloader
from modules.asr import LocalASR
from modules.analyzer import StyleAnalyzer
from modules.script_generator import ScriptGenerator
from modules.video_generator import generate_video, list_voices

asr_engine = None
analyzer = StyleAnalyzer()
script_gen = ScriptGenerator()
downloader = DouyinDownloader()


def get_asr():
    global asr_engine
    if asr_engine is None:
        asr_engine = LocalASR()
    return asr_engine


def step_download(douyin_url):
    if not douyin_url.strip():
        return None, "请输入抖音分享链接"
    try:
        video_path = downloader.download(douyin_url.strip(), method="ytdlp")
        return str(video_path), f"下载完成: {video_path.name}"
    except Exception as e:
        return None, f"下载失败: {e}"


def step_asr(video_path):
    if not video_path:
        return "", "请先下载或上传视频"
    try:
        engine = get_asr()
        transcript = engine.transcribe(Path(video_path))
        return transcript, f"识别完成, 共 {len(transcript)} 字"
    except Exception as e:
        return "", f"识别失败: {e}"


def step_analyze(transcript):
    if not transcript.strip():
        return "{}", "请先获取口播文案"
    try:
        style = analyzer.analyze(transcript)
        return json.dumps(style, ensure_ascii=False, indent=2), "风格分析完成"
    except Exception as e:
        return "{}", f"分析失败: {e}"


def step_generate_script(transcript, style_json, product_name, product_desc, store_desc, duration):
    if not transcript.strip():
        return "{}", "请先获取口播文案"
    if not product_name.strip():
        return "{}", "请输入产品名称"
    try:
        style = json.loads(style_json) if style_json.strip() else {}
        script = script_gen.generate(
            style_analysis=style,
            original_transcript=transcript,
            product_name=product_name,
            product_description=product_desc,
            store_description=store_desc,
            target_duration=int(duration),
        )
        return json.dumps(script, ensure_ascii=False, indent=2), "文案生成完成"
    except Exception as e:
        return "{}", f"生成失败: {e}"


def step_generate_video(script_json, avatar_img, product_imgs, store_imgs, voice_key):
    if not script_json.strip():
        return None, "请先生成文案"
    try:
        script = json.loads(script_json)
        voices = list_voices()
        voice = voices.get(voice_key, "zh-CN-XiaoxiaoNeural")

        output_name = f"result_{uuid.uuid4().hex[:8]}.mp4"
        output_path = RESULT_DIR / output_name

        avatar_path = Path(avatar_img) if avatar_img else None
        product_paths = [Path(p) for p in product_imgs] if product_imgs else None
        store_paths = [Path(p) for p in store_imgs] if store_imgs else None

        result = generate_video(
            script=script,
            avatar_image=avatar_path,
            product_photos=product_paths,
            store_photos=store_paths,
            voice=voice,
            output_path=output_path,
        )
        return str(result), f"视频生成完成: {output_name}"
    except Exception as e:
        return None, f"生成失败: {e}"


def step_refine_script(script_json, feedback):
    if not script_json.strip():
        return "{}", "请先生成文案"
    if not feedback.strip():
        return script_json, "未提供修改意见"
    try:
        script = json.loads(script_json)
        refined = script_gen.refine(script, feedback)
        return json.dumps(refined, ensure_ascii=False, indent=2), "文案调整完成"
    except Exception as e:
        return script_json, f"调整失败: {e}"


def run_full_pipeline(douyin_url, product_name, product_desc, store_desc, avatar_img, product_imgs, store_imgs, voice_key, duration):
    log = []

    def add_log(msg):
        log.append(msg)
        return "\n".join(log)

    if not douyin_url.strip():
        return None, add_log("[ERROR] 请输入抖音分享链接")
    if not product_name.strip():
        return None, add_log("[ERROR] 请输入产品名称")

    add_log("[1/5] 下载抖音视频...")
    try:
        video_path = downloader.download(douyin_url.strip(), method="ytdlp")
        add_log(f"  -> 下载完成: {video_path.name}")
    except Exception as e:
        return None, add_log(f"  -> 下载失败: {e}")

    add_log("[2/5] ASR 语音识别...")
    try:
        engine = get_asr()
        transcript = engine.transcribe(video_path)
        add_log(f"  -> 识别完成, {len(transcript)} 字")
    except Exception as e:
        return None, add_log(f"  -> 识别失败: {e}")

    add_log("[3/5] 风格分析...")
    try:
        style = analyzer.analyze(transcript)
        add_log(f"  -> 风格: {style.get('tone_style', 'unknown')}")
    except Exception as e:
        return None, add_log(f"  -> 分析失败: {e}")

    add_log("[4/5] 生成推广文案...")
    try:
        script = script_gen.generate(
            style_analysis=style,
            original_transcript=transcript,
            product_name=product_name,
            product_description=product_desc,
            store_description=store_desc,
            target_duration=int(duration),
        )
        add_log(f"  -> 标题: {script.get('title', 'N/A')}")
    except Exception as e:
        return None, add_log(f"  -> 生成失败: {e}")

    add_log("[5/5] 合成视频...")
    try:
        voices = list_voices()
        voice = voices.get(voice_key, "zh-CN-XiaoxiaoNeural")
        output_name = f"result_{uuid.uuid4().hex[:8]}.mp4"
        output_path = RESULT_DIR / output_name

        avatar_path = Path(avatar_img) if avatar_img else None
        product_paths = [Path(p) for p in product_imgs] if product_imgs else None
        store_paths = [Path(p) for p in store_imgs] if store_imgs else None

        result = generate_video(
            script=script,
            avatar_image=avatar_path,
            product_photos=product_paths,
            store_photos=store_paths,
            voice=voice,
            output_path=output_path,
        )
        add_log(f"  -> 视频生成完成!")
        return str(result), add_log("[DONE] 全部完成!")
    except Exception as e:
        return None, add_log(f"  -> 生成失败: {e}")


voice_choices = list(list_voices().keys())

with gr.Blocks(title="数字人探店视频生成器") as app:

    gr.Markdown("# 数字人探店视频生成器\n抖音视频 -> ASR -> 风格分析 -> AI文案 -> 数字人视频")

    with gr.Tabs():
        with gr.Tab("一键生成"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 输入")
                    full_url = gr.Textbox(label="抖音分享链接", placeholder="粘贴抖音分享文本或链接", lines=2)
                    full_product = gr.Textbox(label="产品名称", placeholder="如: 芒果干")
                    full_desc = gr.Textbox(label="产品描述", placeholder="描述产品卖点", lines=3)
                    full_store = gr.Textbox(label="店铺描述 (选填)", placeholder="店铺名称/位置/特色", lines=2)
                    with gr.Row():
                        full_avatar = gr.File(label="数字人头像 (选填)", file_types=["image"], type="filepath")
                        full_voice = gr.Dropdown(choices=voice_choices, value="female_warm", label="语音风格")
                    with gr.Row():
                        full_product_imgs = gr.File(label="产品照片 (选填, 多张)", file_types=["image"], type="filepath", file_count="multiple")
                        full_store_imgs = gr.File(label="店铺照片 (选填, 多张)", file_types=["image"], type="filepath", file_count="multiple")
                    full_duration = gr.Slider(minimum=15, maximum=120, value=60, step=5, label="目标时长(秒)")
                    full_btn = gr.Button("一键生成", variant="primary", size="lg")

                with gr.Column(scale=1):
                    gr.Markdown("### 输出")
                    full_log = gr.Textbox(label="运行日志", lines=20, interactive=False)
                    full_video = gr.Video(label="生成的视频")

            full_btn.click(
                fn=run_full_pipeline,
                inputs=[full_url, full_product, full_desc, full_store, full_avatar, full_product_imgs, full_store_imgs, full_voice, full_duration],
                outputs=[full_video, full_log],
            )

        with gr.Tab("分步操作"):
            gr.Markdown("### Step 1: 下载抖音视频")
            with gr.Row():
                step1_url = gr.Textbox(label="抖音分享链接", placeholder="粘贴链接", scale=4)
                step1_btn = gr.Button("下载", scale=1)
            step1_video = gr.Video(label="下载的视频")
            step1_status = gr.Textbox(label="状态", interactive=False)

            step1_btn.click(fn=step_download, inputs=[step1_url], outputs=[step1_video, step1_status])

            gr.Markdown("---\n### Step 2: ASR 语音识别")
            with gr.Row():
                step2_source = gr.Textbox(label="视频路径", placeholder="自动填入或手动输入", scale=4)
                step2_btn = gr.Button("识别", scale=1)
            step2_text = gr.Textbox(label="口播文案", lines=6, interactive=False)
            step2_status = gr.Textbox(label="状态", interactive=False)

            step1_video.change(fn=lambda v: v or "", inputs=[step1_video], outputs=[step2_source])
            step2_btn.click(fn=step_asr, inputs=[step2_source], outputs=[step2_text, step2_status])

            gr.Markdown("---\n### Step 3: 风格分析")
            step3_btn = gr.Button("分析风格")
            step3_style = gr.Textbox(label="风格分析结果 (JSON)", lines=10, interactive=False)
            step3_status = gr.Textbox(label="状态", interactive=False)

            step3_btn.click(fn=step_analyze, inputs=[step2_text], outputs=[step3_style, step3_status])

            gr.Markdown("---\n### Step 4: 生成推广文案")
            step4_product = gr.Textbox(label="产品名称")
            step4_desc = gr.Textbox(label="产品描述", lines=2)
            step4_store = gr.Textbox(label="店铺描述 (选填)")
            step4_duration = gr.Slider(minimum=15, maximum=120, value=60, step=5, label="目标时长(秒)")
            step4_btn = gr.Button("生成文案", variant="primary")
            step4_script = gr.Textbox(label="文案结果 (JSON, 可手动编辑)", lines=14, interactive=True)
            step4_status = gr.Textbox(label="状态", interactive=False)

            step4_feedback = gr.Textbox(label="修改意见 (对当前文案提修改要求)", lines=2)
            step4_refine_btn = gr.Button("调整文案")

            step4_btn.click(
                fn=step_generate_script,
                inputs=[step2_text, step3_style, step4_product, step4_desc, step4_store, step4_duration],
                outputs=[step4_script, step4_status],
            )
            step4_refine_btn.click(
                fn=step_refine_script,
                inputs=[step4_script, step4_feedback],
                outputs=[step4_script, step4_status],
            )

            gr.Markdown("---\n### Step 5: 生成视频")
            step5_avatar = gr.File(label="数字人头像 (选填)", file_types=["image"], type="filepath")
            with gr.Row():
                step5_product_imgs = gr.File(label="产品照片 (多张)", file_types=["image"], type="filepath", file_count="multiple")
                step5_store_imgs = gr.File(label="店铺照片 (多张)", file_types=["image"], type="filepath", file_count="multiple")
            step5_voice = gr.Dropdown(choices=voice_choices, value="female_warm", label="语音风格")
            step5_btn = gr.Button("生成视频", variant="primary")
            step5_video = gr.Video(label="生成的视频")
            step5_status = gr.Textbox(label="状态", interactive=False)

            step5_btn.click(
                fn=step_generate_video,
                inputs=[step4_script, step5_avatar, step5_product_imgs, step5_store_imgs, step5_voice],
                outputs=[step5_video, step5_status],
            )


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(),
    )
