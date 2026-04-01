import json
import os
from typing import Any, Dict, List, Optional, Union

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

JSONType = Union[Dict[str, Any], List[Any]]

load_dotenv()


def _get_api_key() -> Optional[str]:
    try:
        if "OPENAI_API_KEY" in st.secrets:
            secret_key = st.secrets["OPENAI_API_KEY"]
            if secret_key:
                return secret_key
    except Exception:
        pass

    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key

    return None


def is_available() -> bool:
    return bool(_get_api_key())


def _get_client() -> Optional[OpenAI]:
    api_key = _get_api_key()
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def call_openai(prompt: str, max_tokens: int = 1200) -> Optional[str]:
    try:
        client = _get_client()
        if client is None:
            print("⚠️ OPENAI_API_KEY が見つかりません")
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