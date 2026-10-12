# 数字人探店视频生成器

从抖音视频或上传视频 → ASR 语音识别 → DeepSeek 风格分析 → AI 文案生成 → 数字人探店视频

## 架构

```
用户上传视频/抖音链接
        │
        ▼
  ┌─ Playwright 下载 (抖音链接) ─┐
  │  或直接上传视频文件          │
  └──────────────┬──────────────┘
                 ▼
        faster-whisper ASR (本地)
                 │
                 ▼
          DeepSeek 风格分析
                 │
                 ▼
   DeepSeek 文案生成 (根据产品信息)
                 │
                 ▼
    ┌─ edge-tts TTS ── Kling AI 视频生成 ─┐
    │  (本地语音合成)  (AI 生成视频素材)    │
    └────────────────┬────────────────────┘
                     ▼
              moviepy 合成最终视频
```

## 技术栈

| 模块 | 工具 | 说明 |
|------|------|------|
| Web 服务 | FastAPI + HTML | 前端页面 + REST API |
| 视频下载 | Playwright / yt-dlp | 抖音视频下载或本地上传 |
| 语音识别 | faster-whisper (base) | 本地 CPU 运行 |
| 风格分析 | DeepSeek API | 文本分析提取语言风格 |
| 文案生成 | DeepSeek API | 根据风格+产品信息生成推广文案 |
| 语音合成 | edge-tts | 微软本地 TTS，6 种语音可选 |
| 视频生成 | Kling AI API | AI 生成视频素材 |
| 视频合成 | moviepy | 片段合成+字幕+最终输出 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入：

```
DEEPSEEK_API_KEY=你的DeepSeek密钥
KLING_API_KEY=你的可灵AI密钥
DOUYIN_COOKIE=你的抖音Cookie（可选）
```

### 3. 启动服务

```bash
python server.py
```

浏览器打开 http://127.0.0.1:8080

### 4. 使用

**一键生成**：上传抖音链接或视频文件 → 填写产品信息 → 一键完成

**分步操作**：手动控制每个步骤（下载/ASR/分析/文案/视频）

## 语音选项

| 键 | 声音 | 风格 |
|----|------|------|
| female_warm | 晓晓 | 温暖新闻风 |
| female_lively | 晓依 | 活泼卡通风 |
| male_passion | 云健 | 激情运动风 |
| male_lively | 云希 | 阳光活泼风 |
| male_pro | 云扬 | 专业播报风 |
| male_cute | 云夏 | 可爱卡通风 |

## 目录结构

```
├── server.py              # FastAPI 服务入口
├── config.py              # 配置读取
├── main.py                # CLI 旧入口
├── frontend/index.html    # Web 前端页面
├── modules/
│   ├── downloader.py      # 抖音视频下载 (Playwright/yt-dlp)
│   ├── asr.py             # 语音识别 (faster-whisper)
│   ├── analyzer.py        # 风格分析 (DeepSeek)
│   ├── script_generator.py # 文案生成 (DeepSeek)
│   └── video_generator.py # 视频合成 (edge-tts + moviepy)
├── prompts/               # DeepSeek 提示词模板
├── assets/                # 默认数字人头像
├── output/                # 输出目录
│   ├── videos/            # 下载/上传的视频
│   └── result/            # 最终生成视频
└── .env                   # API 密钥配置
```

## 常见问题

**抖音下载失败？** 上传视频文件代替，或更新 DOUYIN_COOKIE。

**ASR 模型下载慢？** 默认用 `base` 模型(~150MB)，自动从 hf-mirror.com 下载。

**Kling API 认证失败？** 在 https://kling.ai/dev 购买 API 资源包并订阅。
