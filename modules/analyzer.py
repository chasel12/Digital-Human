import json
from pathlib import Path
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

console = Console()


class StyleAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        self.model = "deepseek-chat"

    def analyze(self, transcript: str) -> dict:
        prompt_path = Path(__file__).parent.parent / "prompts" / "style_analysis.txt"
        system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

        console.print("[cyan]正在通过 DeepSeek 分析文案风格...[/cyan]")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"以下是探店视频的口播文案，请分析其风格特征:\n\n{transcript}",
                },
            ],
            max_tokens=2000,
            temperature=0.3,
        )

        result_text = response.choices[0].message.content
        console.print("[green][OK] 风格分析完成[/green]")

        parsed = self._parse(result_text)
        console.print(Panel(
            json.dumps(parsed, ensure_ascii=False, indent=2),
            title="风格分析",
            style="green",
        ))
        return parsed

    def _parse(self, text: str) -> dict:
        try:
            json_match = text
            if "```json" in text:
                json_match = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_match = text.split("```")[1].split("```")[0]
            return json.loads(json_match.strip())
        except (json.JSONDecodeError, IndexError):
            return {"raw_analysis": text}
