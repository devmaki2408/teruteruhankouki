def build_issue_prompt(target: str) -> str:
    return f"""
あなたは新規事業開発に強い戦略コンサルタントです。
以下のターゲットが抱えていそうな課題を5件、具体的に抽出してください。

# ターゲット
{target}

# ルール
- 生活者視点で、現実味のある課題を書く
- 課題文は1文で簡潔に書く
- 重複しない
- 必ずJSONのみ返す
- explanations や補足文は不要

# 出力形式
[
  {{"text": "課題1"}},
  {{"text": "課題2"}},
  {{"text": "課題3"}},
  {{"text": "課題4"}},
  {{"text": "課題5"}}
]
""".strip()


def build_more_issue_prompt(target: str, existing_issues: list[str]) -> str:
    existing_text = "\n".join([f"- {x}" for x in existing_issues])

    return f"""
あなたは新規事業開発に強い戦略コンサルタントです。
以下のターゲットについて、既存の課題案と重複しない新しい課題を5件追加で考えてください。

# ターゲット
{target}

# 既存の課題
{existing_text}

# ルール
- 既存の課題と重複しない
- 生活者視点で具体的に書く
- 必ずJSONのみ返す

# 出力形式
[
  {{"text": "追加課題1"}},
  {{"text": "追加課題2"}},
  {{"text": "追加課題3"}},
  {{"text": "追加課題4"}},
  {{"text": "追加課題5"}}
]
""".strip()


def build_idea_prompt(target: str, issue_text: str) -> str:
    return f"""
あなたは新規事業の企画責任者です。
以下のターゲットと課題に対して、事業案を5件考えてください。

# ターゲット
{target}

# 課題
{issue_text}

# ルール
- 事業案は実在しそうなレベルで具体化する
- タイトルは短くわかりやすく
- summary は2〜3文で説明
- score は 0〜100 の整数
- 必ずJSONのみ返す

# 出力形式
[
  {{
    "title": "事業案タイトル",
    "summary": "事業案の概要",
    "score": 80
  }}
]
""".strip()


def build_more_idea_prompt(target: str, issue_text: str, existing_titles: list[str]) -> str:
    existing_text = "\n".join([f"- {x}" for x in existing_titles])

    return f"""
あなたは新規事業の企画責任者です。
以下のターゲットと課題に対して、既存案と重複しない事業案を5件追加で考えてください。

# ターゲット
{target}

# 課題
{issue_text}

# 既存の事業案タイトル
{existing_text}

# ルール
- 既存案と重複しない
- タイトルは短くわかりやすく
- summary は2〜3文
- score は 0〜100 の整数
- 必ずJSONのみ返す

# 出力形式
[
  {{
    "title": "追加事業案タイトル",
    "summary": "追加事業案の概要",
    "score": 72
  }}
]
""".strip()


def build_detail_prompt(title: str, summary: str) -> str:
    return f"""
あなたは事業戦略アナリストです。
以下の事業案について、5Forces分析と推奨人材を整理してください。

# 事業案タイトル
{title}

# 概要
{summary}

# ルール
- five_forces は5項目すべて埋める
- talent は4件出す
- reason は具体的に書く
- 必ずJSONのみ返す

# 出力形式
{{
  "five_forces": {{
    "競合（既存競合との競争）": "説明",
    "新規参入の脅威": "説明",
    "代替品の脅威": "説明",
    "買い手の交渉力": "説明",
    "売り手の交渉力": "説明"
  }},
  "talent": [
    {{
      "role": "推奨人材の役割",
      "reason": "必要な理由"
    }},
    {{
      "role": "推奨人材の役割",
      "reason": "必要な理由"
    }},
    {{
      "role": "推奨人材の役割",
      "reason": "必要な理由"
    }},
    {{
      "role": "推奨人材の役割",
      "reason": "必要な理由"
    }}
  ]
}}
""".strip()