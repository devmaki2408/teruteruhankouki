import json
import os
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

JSONType = Union[Dict[str, Any], List[Any]]


def is_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _get_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def call_openai(prompt: str, max_tokens: int = 1200) -> Optional[str]:
    try:
        client = _get_client()
        if client is None:
            print("⚠️ OPENAI_API_KEY が設定されていません")
            return None

        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": "You must return only valid JSON. Do not include markdown fences or any extra text.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_output_tokens=max_tokens,
        )

        raw_text = getattr(response, "output_text", None)

        if not raw_text:
            raw_text = ""
            for item in getattr(response, "output", []):
                for content in getattr(item, "content", []):
                    if hasattr(content, "text") and content.text:
                        raw_text += content.text

        if not raw_text:
            print("⚠️ AIレスポンスが空です")
            return None

        return raw_text

    except Exception as e:
        print("⚠️ OpenAIエラー:", str(e))
        return None


def parse_json_response(raw_text: Optional[str]) -> Optional[JSONType]:
    if not raw_text:
        return None

    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, (dict, list)):
            return parsed
        return None
    except json.JSONDecodeError:
        print("⚠️ JSONパース失敗")
        print(raw_text)
        return None