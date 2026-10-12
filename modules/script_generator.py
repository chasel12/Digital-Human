import json
from pathlib import Path
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

console = Console()


class ScriptGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        self.model = "deepseek-chat"

    def generate(
        self,
        style_analysis: dict,
        original_transcript: str,
        product_name: str,
        product_description: str,
        store_description: str = "",
        digital_human_desc: str = "",
        target_duration: int = 60,
    ) -> dict:
        prompt_path = Path(__file__).parent.parent / "prompts" / "script_generation.txt"
        system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

        style_text = style_analysis.get("raw_analysis", json.dumps(style_analysis, ensure_ascii=False))

        user_prompt = f"""## 原始探店视频风格分析
{style_text}

## 原始口播文案
{original_transcript}

## 新产品信息
- 产品名称: {product_name}
- 产品描述: {product_description}
- 店铺信息: {store_description or '未提供'}
- 数字人形象要求: {digital_human_desc or '无特定要求'}

请基于原始视频的风格，为新产品生成一个约{target_duration}秒的探店推广口播文案。"""

        console.print("[cyan]正在通过 DeepSeek 生成探店推广文案...[/cyan]")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=3000,
            temperature=0.7,
        )

        result_text = response.choices[0].message.content
        console.print("[green][OK] 文案生成完成[/green]")

        parsed = self._parse(result_text)
        console.print(Panel(
            json.dumps(parsed, ensure_ascii=False, indent=2),
            title="生成的探店文案",
            style="green",
        ))
        return parsed

    def refine(self, script: dict, feedback: str) -> dict:
        console.print("[cyan]正在根据反馈调整文案...[/cyan]")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个短视频文案编辑，请根据用户反馈调整已有的探店推广文案，保持原有风格。",
                },
                {
                    "role": "user",
                    "content": f"当前文案:\n{json.dumps(script, ensure_ascii=False, indent=2)}\n\n修改意见:\n{feedback}",
                },
            ],
            max_tokens=3000,
            temperature=0.7,
        )

        result_text = response.choices[0].message.content
        console.print("[green][OK] 文案调整完成[/green]")
        return self._parse(result_text)

    def _parse(self, text: str) -> dict:
        try:
            json_match = text
            if "```json" in text:
                json_match = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_match = text.split("```")[1].split("```")[0]
            return json.loads(json_match.strip())
        except (json.JSONDecodeError, IndexError):
            return {"title": "探店推广", "raw_script": text}
