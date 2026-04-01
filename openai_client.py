import json
import os
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

JSONType = Union[Dict[str, Any], List[Any]]

_api_key = os.getenv("OPENAI_API_KEY")

if not _api_key:
    raise ValueError("OPENAI_API_KEY が設定されていません")

_client = OpenAI(api_key=_api_key)
from prompts import (
    build_issue_generation_prompt,
    build_more_issue_generation_prompt,
    build_idea_generation_prompt,
    build_more_idea_generation_prompt,
    build_five_forces_prompt,
    build_member_reason_prompt,
)

def generate_json(prompt: str) -> Optional[JSONType]:
    try:
        response = _client.responses.create(
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
            text={"format": {"type": "json_object"}},
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

        try:
            parsed = json.loads(raw_text)
            return parsed if isinstance(parsed, (dict, list)) else None
        except json.JSONDecodeError:
            print("⚠️ JSONパース失敗")
            print(raw_text)
            return None

    except Exception as e:
        print("⚠️ OpenAIエラー:", str(e))
        return None


def fetch_issues_from_ai(target: str) -> Optional[Dict[str, Any]]:
    prompt = build_issue_generation_prompt(target)
    return generate_json(prompt)


def fetch_more_issues_from_ai(target: str, existing_issues: list) -> Optional[Dict[str, Any]]:
    prompt = build_more_issue_generation_prompt(
        target,
        json.dumps(existing_issues, ensure_ascii=False, indent=2)
    )
    return generate_json(prompt)


def fetch_ideas_from_ai(target: str, issue_title: str, issue_description: str) -> Optional[Dict[str, Any]]:
    prompt = build_idea_generation_prompt(target, issue_title, issue_description)
    return generate_json(prompt)

def fetch_more_ideas_from_ai(
    target: str,
    issue_title: str,
    issue_description: str,
    existing_ideas: list,
) -> Optional[Dict[str, Any]]:
    prompt = build_more_idea_generation_prompt(
        target,
        issue_title,
        issue_description,
        json.dumps(existing_ideas, ensure_ascii=False, indent=2),
    )
    return generate_json(prompt)


def fetch_five_forces_from_ai(idea_title: str, idea_overview: str) -> Optional[Dict[str, Any]]:
    prompt = build_five_forces_prompt(idea_title, idea_overview)
    return generate_json(prompt)


def fetch_member_reason_from_ai(
    idea_title: str,
    member_name: str,
    member_skills: list,
) -> Optional[Dict[str, Any]]:
    prompt = build_member_reason_prompt(
        idea_title,
        member_name,
        json.dumps(member_skills, ensure_ascii=False, indent=2),
    )
    return generate_json(prompt)