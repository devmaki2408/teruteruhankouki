# crawler.py
# ============================================================
# 指定 URL の本文テキストを取得・抽出するユーティリティ。
# 用途例：
#   - 競合調査用ページの本文取得
#   - ニュース記事の自動収集
#   - プロンプトへの参考情報注入
# ============================================================

import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

# デフォルト設定
DEFAULT_TIMEOUT = 10       # 秒
DEFAULT_MAX_CHARS = 3000   # 本文の最大文字数（プロンプト長さ制御用）
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BusinessIdeaBot/1.0; "
        "+https://example.com/bot)"
    )
}


def fetch_page(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    """
    URL から HTML を取得して文字列で返す。
    失敗時は None を返す。
    """
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except requests.RequestException as e:
        print(f"[crawler] fetch失敗 {url}: {e}")
        return None


def extract_text(html: str, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """
    HTML から本文テキストを抽出して返す。
    script / style タグを除去し、空白を正規化する。
    """
    soup = BeautifulSoup(html, "html.parser")

    # 不要タグを除去
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # <article> や <main> があれば優先的に使う
    main_content = soup.find("article") or soup.find("main") or soup.body or soup
    raw_text = main_content.get_text(separator="\n")

    # 連続する空白・改行を正規化
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    text = "\n".join(lines)

    return text[:max_chars]


def crawl(url: str, max_chars: int = DEFAULT_MAX_CHARS) -> Optional[str]:
    """
    URL を取得して本文テキストを返すメイン関数。
    失敗時は None を返す。
    """
    html = fetch_page(url)
    if html is None:
        return None
    return extract_text(html, max_chars=max_chars)


def crawl_multiple(urls: list[str], delay: float = 1.0, max_chars: int = DEFAULT_MAX_CHARS) -> list[dict]:
    """
    複数 URL をクロールし、結果をリストで返す。
    サーバー負荷軽減のため delay 秒のウェイトを挟む。

    Returns
    -------
    list[dict]
        [{"url": str, "text": str | None}, ...]
    """
    results = []
    for i, url in enumerate(urls):
        if i > 0:
            time.sleep(delay)
        text = crawl(url, max_chars=max_chars)
        results.append({"url": url, "text": text})
    return results