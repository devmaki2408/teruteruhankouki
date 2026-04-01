"""
app.py — Tech0 Search v2.0「BizSpark × IdeaForge」
新規事業アイデア創出アプリ（Gemini AI + 学習統合構造版）

【画面フロー】 ※ BizSpark AI の構成を採用
  landing     : ターゲット入力
  issue_list  : AI生成 課題一覧（10件）
  idea_list   : AI生成 事業案一覧（10件）
  detail      : 詳細 / 分析 / 推奨人材 / 知識ベース検索

【設計方針】
- UI/CSSはIdeaForge（青系・Syne/DM Sans・カード設計）を維持
- 画面ロジックはBizSpark AIの遷移構造を採用
- AI呼び出しは generate_content() に集約（Gemini / OpenAI 差し替え可）
- crawler / database / ranking の接続ポイントは ★INTEGRATION POINT で統一

【他メンバーとの統合時の注意】
- モックデータは MOCK_* セクションに集約
- DB / crawler / ranking の呼び出しは do_crawl_and_register() / get_knowledge_pages() に集約
- st.session_state のキー一覧は init_session() を参照
"""

import os
import json
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 外部モジュールの条件付きインポート
# ★INTEGRATION POINT: 各ファイルが完成したら try/except を削除する
# ─────────────────────────────────────────────────────────────────────────────
try:
    from database import init_db, get_all_pages, insert_page, log_search, DB_PATH
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

try:
    from ranking import get_engine, rebuild_index
    RANKING_AVAILABLE = True
except ImportError:
    RANKING_AVAILABLE = False

try:
    from crawler import crawl_url
    CRAWLER_AVAILABLE = True
except ImportError:
    CRAWLER_AVAILABLE = False

# DB が使えるなら起動時に初期化する
if DB_AVAILABLE:
    init_db()

# ─────────────────────────────────────────────────────────────────────────────
# Gemini API 設定
# 環境変数 GEMINI_API_KEY または Streamlit Secrets から取得する
# ─────────────────────────────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
    if api_key:
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        AI_AVAILABLE = True
    else:
        AI_AVAILABLE = False
except Exception:
    AI_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# アプリ設定
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BizSpark AI — 新規事業アイデア創出",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# グローバル CSS（IdeaForge デザインシステム）
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

:root {
    --blue-deep:   #0B1F3A;
    --blue-mid:    #1B3F72;
    --blue-accent: #2C6FFF;
    --blue-light:  #EBF1FF;
    --teal:        #00C6B3;
    --amber:       #F5A623;
    --white:       #FFFFFF;
    --gray-50:     #F8FAFC;
    --gray-100:    #EFF2F6;
    --gray-300:    #CBD5E0;
    --gray-500:    #718096;
    --gray-600:    #4A5568;
    --radius-lg:   16px;
    --radius-xl:   24px;
    --shadow-card: 0 4px 24px rgba(11,31,58,0.08);
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--gray-50) !important;
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"] > div { gap: 0 !important; }

/* ── ナビバー ── */
.nav-bar {
    background: var(--blue-deep);
    padding: 18px 48px;
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 100;
}
.nav-logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800; font-size: 22px;
    color: var(--white); letter-spacing: -0.5px;
}
.nav-logo span { color: var(--teal); }
.nav-badges { display: flex; gap: 8px; align-items: center; }
.nav-badge {
    background: rgba(44,111,255,0.25); color: var(--blue-light);
    font-size: 11px; font-weight: 600;
    padding: 4px 12px; border-radius: 100px; letter-spacing: 0.5px;
}
.integration-badge {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 600;
    padding: 4px 10px; border-radius: 100px;
}
.integration-badge.ok   { background: rgba(0,198,179,0.18); color: var(--teal); }
.integration-badge.mock { background: rgba(245,166,35,0.18); color: var(--amber); }

/* ── メインラップ ── */
.main-wrap { padding: 40px 48px; }

/* ── ヒーロー ── */
.hero {
    background: linear-gradient(135deg, var(--blue-deep) 0%, var(--blue-mid) 100%);
    border-radius: var(--radius-xl);
    padding: 72px 64px; color: var(--white);
    position: relative; overflow: hidden;
}
.hero::before {
    content: ''; position: absolute;
    top: -80px; right: -80px; width: 320px; height: 320px;
    border-radius: 50%; background: rgba(44,111,255,0.15);
}
.hero::after {
    content: ''; position: absolute;
    bottom: -60px; left: 30%; width: 200px; height: 200px;
    border-radius: 50%; background: rgba(0,198,179,0.10);
}
.hero-eyebrow {
    font-size: 11px; font-weight: 700; letter-spacing: 2.5px;
    color: var(--teal); text-transform: uppercase; margin-bottom: 16px;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 52px; font-weight: 800; line-height: 1.1;
    margin-bottom: 20px; max-width: 640px;
}
.hero-title em { color: var(--teal); font-style: normal; }
.hero-desc {
    font-size: 16px; line-height: 1.75; opacity: 0.8;
    max-width: 520px; margin-bottom: 0;
}

/* ── セクションタイトル ── */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 30px; font-weight: 800;
    color: var(--blue-deep); line-height: 1.2; margin-bottom: 6px;
}
.section-sub {
    font-size: 14px; color: var(--gray-600);
    margin-bottom: 28px; line-height: 1.7;
}

/* ── カード ── */
.card {
    background: var(--white); border-radius: var(--radius-xl);
    box-shadow: var(--shadow-card); padding: 28px 32px;
    border: 1.5px solid var(--gray-100);
    transition: box-shadow 0.2s, border-color 0.2s;
}
.card:hover {
    box-shadow: 0 8px 32px rgba(11,31,58,0.13); border-color: var(--blue-light);
}

/* ── 課題カード ── */
.issue-card {
    background: var(--white); border-radius: var(--radius-lg);
    border: 1.5px solid var(--gray-100); padding: 22px 26px;
    transition: all 0.18s;
}
.issue-card:hover { border-color: var(--blue-accent); box-shadow: 0 4px 20px rgba(44,111,255,0.10); }
.issue-tag {
    display: inline-block; background: var(--blue-light); color: var(--blue-accent);
    font-size: 10px; font-weight: 700; padding: 2px 9px;
    border-radius: 100px; margin-bottom: 8px; letter-spacing: 0.5px; text-transform: uppercase;
}
.issue-title {
    font-family: 'Syne', sans-serif; font-size: 16px; font-weight: 700;
    color: var(--blue-deep); margin-bottom: 6px; line-height: 1.35;
}
.issue-desc { font-size: 13px; color: var(--gray-600); line-height: 1.65; margin-bottom: 10px; }

/* ── アイデアカード ── */
.idea-card {
    background: var(--white); border-radius: var(--radius-xl);
    border: 1.5px solid var(--gray-100); padding: 26px 28px;
    transition: all 0.18s; height: 100%;
}
.idea-card:hover { border-color: var(--blue-accent); box-shadow: 0 8px 28px rgba(44,111,255,0.12); }
.idea-tag {
    display: inline-block; background: var(--blue-light); color: var(--blue-accent);
    font-size: 10px; font-weight: 700; padding: 2px 9px;
    border-radius: 100px; margin-bottom: 10px; letter-spacing: 0.5px;
}
.idea-title {
    font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 700;
    color: var(--blue-deep); margin-bottom: 10px; line-height: 1.3;
}
.idea-desc { font-size: 13px; color: var(--gray-600); line-height: 1.7; margin-bottom: 14px; }
.idea-meta { display: flex; gap: 8px; flex-wrap: wrap; }
.pill {
    font-size: 11px; font-weight: 500; padding: 3px 10px;
    border-radius: 100px; background: var(--gray-100); color: var(--gray-600);
}
.pill.score  { background: rgba(0,198,179,0.12); color: var(--teal); font-weight: 700; }
.pill.accent { background: var(--blue-light); color: var(--blue-accent); font-weight: 600; }

/* ── スコアバッジ ── */
.score-badge {
    background: var(--blue-light); color: var(--blue-accent);
    padding: 10px 18px; border-radius: 100px;
    font-family: 'Syne', sans-serif; font-weight: 800; font-size: 22px;
    display: inline-block; text-align: center;
}

/* ── 人材カード ── */
.person-card {
    background: var(--white); border-radius: var(--radius-lg);
    border: 1.5px solid var(--gray-100); padding: 20px; height: 100%;
    transition: all 0.18s;
}
.person-card:hover { border-color: var(--teal); }
.person-name {
    font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 700;
    color: var(--blue-deep); margin-bottom: 4px;
}
.person-skills { font-size: 12px; color: var(--gray-600); margin-bottom: 10px; }
.person-reason { font-size: 11px; color: var(--blue-accent); line-height: 1.6; }

/* ── 検索結果カード ── */
.result-card {
    background: var(--white); border-radius: var(--radius-lg);
    border: 1px solid var(--gray-100); padding: 18px 22px; margin-bottom: 10px;
    transition: box-shadow 0.15s;
}
.result-card:hover { box-shadow: 0 4px 16px rgba(11,31,58,0.08); }
.result-title { font-family:'Syne',sans-serif; font-size:15px; font-weight:700; color:var(--blue-deep); }
.result-url   { font-size:11px; color:var(--blue-accent); margin:2px 0 6px; word-break:break-all; }
.result-desc  { font-size:12px; color:var(--gray-600); line-height:1.6; }
.result-score {
    float: right; background: var(--blue-light); color: var(--blue-accent);
    font-size:11px; font-weight:700; padding:2px 9px; border-radius:100px;
}

/* ── ボタン ── */
.stButton > button {
    background: var(--blue-accent) !important; color: var(--white) !important;
    border: none !important; border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important;
    font-size: 14px !important; padding: 12px 28px !important; transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #1A5CE8 !important;
    box-shadow: 0 4px 16px rgba(44,111,255,0.38) !important;
    transform: translateY(-1px) !important;
}

/* ── インプット ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    border-radius: 10px !important; border-color: var(--gray-100) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── タブ ── */
[data-testid="stTabs"] [role="tablist"] {
    background: var(--gray-100); border-radius: 12px; padding: 4px; gap: 4px;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 8px !important; font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: var(--white) !important; color: var(--blue-accent) !important;
}

/* ── フッター ── */
.footer {
    text-align: center; padding: 32px; color: var(--gray-300); font-size: 12px;
    border-top: 1px solid var(--gray-100); margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MOCK_DATA — モックデータをここに集約
# ★INTEGRATION POINT: AI / DB に差し替えるときはこのセクションを置き換える
# ─────────────────────────────────────────────────────────────────────────────
MOCK_PERSONNEL = [
    {"name": "田中 健一", "skills": ["新規事業開発", "PM"],   "mbo": "新規プロジェクト立ち上げ成功"},
    {"name": "佐藤 美咲", "skills": ["UI/UX", "リサーチ"],    "mbo": "アプリ改善でCVR 20%向上"},
    {"name": "鈴木 翔太", "skills": ["法人営業", "提携"],      "mbo": "大手提携5件成立"},
    {"name": "高橋 結衣", "skills": ["技術選定", "インフラ"],  "mbo": "大規模システム安定稼働"},
]

MOCK_ISSUES = [
    {"id": "i1", "title": "育児と仕事の両立による時間不足",     "description": "保育園の送迎・家事・仕事が重なり、自分の時間がほぼゼロになっている。", "relationship": "直接課題"},
    {"id": "i2", "title": "育児情報の分散と信頼性の低さ",       "description": "SNS・育児書・病院で情報が異なり、何を信じればよいか判断できない。",     "relationship": "情報課題"},
    {"id": "i3", "title": "緊急時の頼れるサービスの不足",       "description": "急な残業・体調不良時に子どもを預けられる場所がない。",                 "relationship": "サポート課題"},
    {"id": "i4", "title": "夫婦間の育児負担の偏り",            "description": "片方に育児が集中し、夫婦関係に摩擦が生まれる。",                       "relationship": "関係性課題"},
    {"id": "i5", "title": "子どもの習い事・教育投資の最適化",   "description": "どの習い事がわが子に合うか情報が少なく、費用対効果が不透明。",           "relationship": "投資課題"},
]

MOCK_IDEAS = [
    {"id": "a1", "title": "AI育児アシスタントSaaS",        "overview": "月齢・発達記録をもとにパーソナライズされた育児提案を自動生成。", "solution": "LLM + 保健師監修DB",   "value": "育児意思決定時間を50%削減", "score": 91, "reason": "市場規模・実現可能性ともに高い"},
    {"id": "a2", "title": "共働き世帯向け家事代行マッチング", "overview": "隙間時間を持つ近隣住民と家事ニーズをリアルタイムでマッチング。",  "solution": "位置情報 + 評価システム", "value": "月平均8時間の家事時間を創出", "score": 84, "reason": "競合が多いが差別化余地あり"},
    {"id": "a3", "title": "育児ナレッジ共有コミュニティ",    "overview": "同月齢・同地域の親同士が知見をシェアするSNS型プラットフォーム。",  "solution": "UGC + 専門家Q&A",        "value": "孤育て解消・情報の信頼性向上", "score": 77, "reason": "エンゲージメント維持が課題"},
]

MOCK_PAGES = [
    {"id": 1, "url": "https://example.com/dx-report", "title": "製造業DX推進レポート 2024",   "description": "国内製造業500社のDX現状調査。",           "word_count": 3200, "crawled_at": "2025-03-01", "relevance_score": 88.5, "base_score": 72.0, "keywords": "DX,製造業,IoT"},
    {"id": 2, "url": "https://example.com/iot-case",  "title": "IoT導入事例：予知保全の実装", "description": "振動センサー+エッジAIで異常検知を実現。", "word_count": 5100, "crawled_at": "2025-02-15", "relevance_score": 76.3, "base_score": 61.0, "keywords": "IoT,予知保全,エッジAI"},
]

# ─────────────────────────────────────────────────────────────────────────────
# セッション初期化
# ─────────────────────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "step":           "landing",   # landing / issue_list / idea_list / detail
        "target":         "",
        "issues":         [],
        "selected_issue": None,
        "ideas":          [],
        "selected_idea":  None,
        "search_query":   "",
        "index_ready":    False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ─────────────────────────────────────────────────────────────────────────────
# AI 呼び出し関数
# ★INTEGRATION POINT: OpenAI / Azure に差し替える場合はここだけ変更する
# ─────────────────────────────────────────────────────────────────────────────
def generate_content(prompt: str, schema_desc: str):
    """
    Gemini API を呼んで JSON を返す。
    API キーがなければ None を返す（呼び出し元でモックにフォールバック）。

    ★OpenAI に差し替える場合:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"user","content": full_prompt}]
        )
        return json.loads(resp.choices[0].message.content)
    """
    if not AI_AVAILABLE:
        return None

    full_prompt = (
        f"{prompt}\n\n"
        f"以下のJSON形式のみで出力してください（コードブロック・前置き不要）:\n{schema_desc}"
    )
    try:
        response = gemini_model.generate_content(full_prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text)
    except Exception as e:
        st.error(f"AI生成エラー: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# データ取得関数（差し替えポイント群）
# ─────────────────────────────────────────────────────────────────────────────
def fetch_issues(target: str) -> list:
    """
    ターゲットから課題10件を生成する。
    ★INTEGRATION POINT: ranking.py の knowledge search と組み合わせ可能。
    """
    schema = '[{"id":"str","title":"str","description":"str","relationship":"str"}] — 10件。idはi1〜i10。'
    result = generate_content(
        f"ターゲット「{target}」が日常で抱える課題を10件、事業機会視点で列挙してください",
        schema,
    )
    return result if result else MOCK_ISSUES


def fetch_ideas(issue_title: str) -> list:
    """
    選択した課題から事業案10件を生成する。
    ★INTEGRATION POINT: DB登録済みページのコンテキストを加えることで精度向上可能。
      例: pages = get_all_pages()[:5]; context = "\n".join(p["title"] for p in pages)
    """
    schema = '[{"id":"str","title":"str","overview":"str","solution":"str","value":"str","score":85,"reason":"str"}] — 10件。'
    result = generate_content(
        f"課題「{issue_title}」を解決する新規事業案を10件立案してください",
        schema,
    )
    return result if result else MOCK_IDEAS


def get_knowledge_pages(query: str) -> list:
    """
    知識ベースをTF-IDF検索する。
    ★INTEGRATION POINT: ranking.py の SearchEngine.search() に接続済み。
    """
    if RANKING_AVAILABLE and st.session_state.get("index_ready"):
        engine = get_engine()
        results = engine.search(query, top_n=8)
        if DB_AVAILABLE:
            log_search(query, len(results))
        return results
    q = query.lower()
    filtered = [p for p in MOCK_PAGES if q in p["title"].lower() or q in p["description"].lower()]
    return filtered if filtered else MOCK_PAGES


def do_crawl_and_register(url: str) -> dict:
    """
    クロール → DB保存 → インデックス再構築を一括実行する。
    ★INTEGRATION POINT: crawler.py + database.py + ranking.py の統合ポイント。
    """
    if not CRAWLER_AVAILABLE:
        return {"crawl_status": "error", "url": url, "title": "クローラー未接続（モック）"}
    result = crawl_url(url)
    if result.get("crawl_status") == "success" and DB_AVAILABLE:
        insert_page(result)
        pages = get_all_pages()
        rebuild_index(pages)
        st.session_state.index_ready = True
    return result


# ─────────────────────────────────────────────────────────────────────────────
# UI部品
# ─────────────────────────────────────────────────────────────────────────────
def render_navbar():
    b = lambda ok, label: (
        f'<span class="integration-badge ok">✓ {label}</span>' if ok
        else f'<span class="integration-badge mock">○ {label}</span>'
    )
    badges = b(DB_AVAILABLE, "DB") + " " + b(RANKING_AVAILABLE, "Ranking") + " " + b(CRAWLER_AVAILABLE, "Crawler") + " " + b(AI_AVAILABLE, "Gemini")
    st.markdown(f"""
    <div class="nav-bar">
        <div class="nav-logo">Biz<span>Spark</span> AI</div>
        <div class="nav-badges">
            {badges}
            <span class="nav-badge">Tech0 WEEK4</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 1: ランディング
# ─────────────────────────────────────────────────────────────────────────────
def render_landing():
    st.markdown("""
    <div class="main-wrap">
      <div class="hero">
        <div class="hero-eyebrow">PROJECT ZERO — WEEK 4 · AI-Powered</div>
        <div class="hero-title">ターゲットを入れると、<br><em>AI が事業案を立案。</em></div>
        <div class="hero-desc">
          課題の発見 → 事業案10件の生成 → 推奨メンバーの提示まで、
          Gemini AI が一貫してサポート。社内知識ベース（TF-IDF）との連携も可能です。
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        target_input = st.text_input(
            "🎯 ターゲットを入力してください",
            placeholder="例：30代共働き、都内在住、子どもあり",
        )
        if not AI_AVAILABLE:
            st.warning("⚠️ GEMINI_API_KEY が未設定のため、モックデータで動作します。")
        if st.button("⚡ 課題を発見する", use_container_width=True, type="primary"):
            if target_input:
                st.session_state.target = target_input
                with st.spinner("AIが課題を抽出中…"):
                    st.session_state.issues = fetch_issues(target_input)
                st.session_state.step = "issue_list"
                st.rerun()
            else:
                st.error("ターゲットを入力してください")

    # アーキテクチャ説明
    st.markdown('<div class="main-wrap" style="padding-top:0;">', unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
        <div style="font-family:'Syne',sans-serif;font-size:17px;font-weight:700;color:var(--blue-deep);margin-bottom:14px;">
            🏗️ システム構成
        </div>
        <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--gray-600);line-height:1.8;">
            <div><b style="color:var(--blue-accent);">Gemini AI</b><br>課題・事業案の生成<br>JSON構造化出力</div>
            <div style="color:var(--gray-300);align-self:center;font-size:20px;">+</div>
            <div><b style="color:var(--blue-accent);">crawler.py</b><br>URLからページ取得<br>タイトル・本文抽出</div>
            <div style="color:var(--gray-300);align-self:center;font-size:20px;">→</div>
            <div><b style="color:var(--blue-accent);">database.py</b><br>SQLite CRUD<br>search_logs管理</div>
            <div style="color:var(--gray-300);align-self:center;font-size:20px;">→</div>
            <div><b style="color:var(--blue-accent);">ranking.py</b><br>TF-IDFインデックス<br>コサイン類似度検索</div>
            <div style="color:var(--gray-300);align-self:center;font-size:20px;">→</div>
            <div><b style="color:var(--blue-accent);">app.py</b><br>UI・画面遷移制御<br>各モジュールを仲介</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 2: 課題一覧
# ─────────────────────────────────────────────────────────────────────────────
def render_issue_list():
    st.markdown(f"""
    <div class="main-wrap">
        <div style="font-size:13px;color:var(--blue-accent);font-weight:600;margin-bottom:6px;">
            🎯 ターゲット: {st.session_state.target}
        </div>
        <div class="section-title">AIが提案する課題候補</div>
        <div class="section-sub">
            {len(st.session_state.issues)} 件の課題を生成しました。解決したい課題を1つ選んでください。
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="padding:0 48px 16px;">', unsafe_allow_html=True)
    if st.button("🔄 別の課題を10件生成"):
        with st.spinner("再生成中…"):
            st.session_state.issues = fetch_issues(st.session_state.target)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:0 48px;">', unsafe_allow_html=True)
    for issue in st.session_state.issues:
        st.markdown(f"""
        <div class="issue-card">
            <span class="issue-tag">{issue.get('relationship','課題')}</span>
            <div class="issue-title">{issue['title']}</div>
            <div class="issue-desc">{issue['description']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"この課題で事業案を生成 →", key=f"issue_{issue['id']}"):
            st.session_state.selected_issue = issue
            with st.spinner("AIが事業案を立案中…"):
                st.session_state.ideas = fetch_ideas(issue["title"])
            st.session_state.step = "idea_list"
            st.rerun()
        st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:8px 48px 0;">', unsafe_allow_html=True)
    if st.button("← 最初に戻る"):
        st.session_state.step = "landing"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 3: 事業案一覧
# ─────────────────────────────────────────────────────────────────────────────
def render_idea_list():
    issue = st.session_state.selected_issue
    st.markdown(f"""
    <div class="main-wrap">
        <div style="font-size:13px;color:var(--blue-accent);font-weight:600;margin-bottom:4px;">
            🎯 {st.session_state.target} &nbsp;/&nbsp; ⚠️ {issue['title']}
        </div>
        <div class="section-title">AIが提案する新規事業案</div>
        <div class="section-sub">
            {len(st.session_state.ideas)} 件の事業案を生成しました。詳細を確認する案を選んでください。
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="padding:0 48px;">', unsafe_allow_html=True)
    for idea in st.session_state.ideas:
        col_text, col_score = st.columns([5, 1], gap="medium")
        with col_text:
            st.markdown(f"""
            <div class="idea-card">
                <span class="idea-tag">事業案</span>
                <div class="idea-title">{idea['title']}</div>
                <div class="idea-desc">
                    <b>概要:</b> {idea['overview']}<br>
                    <b>解決策:</b> {idea['solution']}<br>
                    <span style="font-size:12px;color:var(--gray-500);">{idea['reason']}</span>
                </div>
                <div class="idea-meta">
                    <span class="pill accent">提供価値: {idea['value']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_score:
            st.markdown(f"""
            <div style="display:flex;flex-direction:column;align-items:center;gap:12px;padding-top:24px;">
                <div class="score-badge">{idea['score']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("詳細 →", key=f"idea_{idea['id']}", use_container_width=True):
                st.session_state.selected_idea = idea
                # ★INTEGRATION POINT: 選択アイデアのタイトルで知識ベースを自動検索
                st.session_state.search_query = idea["title"]
                st.session_state.step = "detail"
                st.rerun()
        st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:8px 48px 0;">', unsafe_allow_html=True)
    if st.button("← 課題選択に戻る"):
        st.session_state.step = "issue_list"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 4: 詳細 / 分析 / 推奨人材 / 知識ベース検索
# ─────────────────────────────────────────────────────────────────────────────
def render_detail():
    idea = st.session_state.selected_idea

    st.markdown(f"""
    <div class="main-wrap">
        <div style="font-size:13px;color:var(--blue-accent);font-weight:600;margin-bottom:6px;">
            🎯 {st.session_state.target} &nbsp;/&nbsp; ⚠️ {st.session_state.selected_issue['title']}
        </div>
        <div class="section-title">{idea['title']}</div>
        <div class="section-sub">{idea['overview']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="padding:0 48px;">', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 事業詳細", "📊 分析結果", "👥 推奨メンバー", "🔍 知識ベース"])

    # ── タブ1: 事業詳細 ─────────────────────────────────────────
    with tab1:
        st.markdown(f"""
        <div class="card" style="margin-top:16px;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px;">
                <div style="background:var(--gray-50);border-radius:12px;padding:16px;">
                    <div style="font-size:11px;color:var(--gray-600);">解決策</div>
                    <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:700;color:var(--blue-deep);margin-top:4px;">{idea['solution']}</div>
                </div>
                <div style="background:var(--gray-50);border-radius:12px;padding:16px;">
                    <div style="font-size:11px;color:var(--gray-600);">提供価値</div>
                    <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:700;color:var(--blue-deep);margin-top:4px;">{idea['value']}</div>
                </div>
                <div style="background:var(--gray-50);border-radius:12px;padding:16px;">
                    <div style="font-size:11px;color:var(--gray-600);">AIスコア</div>
                    <div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:var(--teal);margin-top:2px;">{idea['score']}</div>
                </div>
                <div style="background:var(--gray-50);border-radius:12px;padding:16px;">
                    <div style="font-size:11px;color:var(--gray-600);">採点理由</div>
                    <div style="font-size:13px;color:var(--blue-deep);margin-top:4px;line-height:1.6;">{idea['reason']}</div>
                </div>
            </div>
            <div style="background:var(--blue-light);border-radius:12px;padding:16px;">
                <div style="font-size:12px;font-weight:600;color:var(--blue-accent);margin-bottom:4px;">💡 収益化イメージ</div>
                <div style="font-size:13px;color:var(--blue-deep);">
                    サブスクリプション（月額課金）+ 法人向けAPI提供。
                    初期はフリーミアムでユーザー獲得、DAU増加後にプレミアムプランへ誘導。
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── タブ2: 分析結果 ─────────────────────────────────────────
    with tab2:
        col_p, col_s, col_f = st.columns(3, gap="medium")
        with col_p:
            st.markdown("""
            <div class="card" style="margin-top:16px;">
                <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:15px;color:var(--blue-deep);margin-bottom:10px;">🌍 PEST分析</div>
                <div style="font-size:13px;color:var(--gray-600);line-height:1.8;">
                    <b>P:</b> 規制緩和・働き方改革推進<br>
                    <b>E:</b> 共働き世帯増加・可処分所得減少<br>
                    <b>S:</b> 少子高齢化・孤育て問題深刻化<br>
                    <b>T:</b> AI・スマートフォン普及
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_s:
            st.markdown("""
            <div class="card" style="margin-top:16px;">
                <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:15px;color:var(--blue-deep);margin-bottom:10px;">⚖️ SWOT</div>
                <div style="font-size:13px;color:var(--gray-600);line-height:1.8;">
                    <b>強み:</b> 既存顧客基盤・データ蓄積<br>
                    <b>弱み:</b> 認知度・初期コスト<br>
                    <b>機会:</b> 市場拡大・補助金活用<br>
                    <b>脅威:</b> 大手参入・規制変更
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_f:
            st.markdown("""
            <div class="card" style="margin-top:16px;">
                <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:15px;color:var(--blue-deep);margin-bottom:10px;">🔴 5 Forces</div>
                <div style="font-size:13px;color:var(--gray-600);line-height:1.8;">
                    <b>新規参入:</b> 低〜中<br>
                    <b>代替品:</b> 中<br>
                    <b>買い手交渉力:</b> 中<br>
                    <b>売い手交渉力:</b> 低<br>
                    <b>競合:</b> 中〜高
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── タブ3: 推奨メンバー ─────────────────────────────────────
    with tab3:
        st.markdown("""
        <div style="margin:16px 0 14px;">
            <div style="font-family:'Syne',sans-serif;font-size:17px;font-weight:700;color:var(--blue-deep);">
                👥 推奨プロジェクトメンバー（4名）
            </div>
            <div style="font-size:12px;color:var(--gray-500);margin-top:3px;">
                ★INTEGRATION POINT: 社内人材DBと接続することで実メンバーをレコメンド可能
            </div>
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns(4, gap="medium")
        for i, person in enumerate(MOCK_PERSONNEL):
            with cols[i]:
                skills_str = "・".join(person["skills"])
                st.markdown(f"""
                <div class="person-card">
                    <div class="person-name">{person['name']}</div>
                    <div class="person-skills">{skills_str}</div>
                    <div style="border-top:1px solid var(--gray-100);margin:8px 0;"></div>
                    <div class="person-reason">
                        <b>MBO:</b> {person['mbo']}<br>
                        <span style="margin-top:6px;display:block;">
                            適任理由: {idea['title']}に必要なスキルセットを保有
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── タブ4: 知識ベース検索 + クローラー ─────────────────────
    with tab4:
        st.markdown("""
        <div style="margin:16px 0 12px;">
            <div style="font-family:'Syne',sans-serif;font-size:17px;font-weight:700;color:var(--blue-deep);">
                🔍 知識ベース検索（TF-IDF）
            </div>
            <div style="font-size:12px;color:var(--gray-500);margin-top:3px;">
                ★INTEGRATION POINT: ranking.py + database.py に接続済み
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_q, col_btn = st.columns([4, 1])
        with col_q:
            search_query = st.text_input(
                "キーワード",
                value=st.session_state.search_query,
                placeholder="例: IoT, DX, SaaS",
                label_visibility="collapsed",
            )
        with col_btn:
            if st.button("🔍 検索", use_container_width=True):
                st.session_state.search_query = search_query

        if st.session_state.search_query:
            # ★INTEGRATION POINT: ranking.py の engine.search() を呼ぶ
            results = get_knowledge_pages(st.session_state.search_query)
            st.markdown(f"**{len(results)} 件**の関連ページ")
            for page in results:
                kw = page.get("keywords", "") or ""
                kw_pills = "".join([
                    f'<span class="pill" style="font-size:10px;">{k.strip()}</span>'
                    for k in kw.split(",") if k.strip()
                ][:4])
                st.markdown(f"""
                <div class="result-card">
                    <span class="result-score">{page.get('relevance_score','—')}</span>
                    <div class="result-title">{page['title']}</div>
                    <div class="result-url">🔗 {page['url']}</div>
                    <div class="result-desc">{page.get('description','')[:120]}…</div>
                    <div class="idea-meta" style="margin-top:8px;">{kw_pills}</div>
                </div>
                """, unsafe_allow_html=True)

        # クローラー
        st.markdown("""
        <div style="margin-top:24px;margin-bottom:10px;">
            <div style="font-family:'Syne',sans-serif;font-size:16px;font-weight:700;color:var(--blue-deep);">
                🤖 クローラー（知識ベースに追加）
            </div>
        </div>
        """, unsafe_allow_html=True)
        crawl_url_input = st.text_input(
            "URL",
            placeholder="https://example.com/article",
            label_visibility="collapsed",
            key="crawl_url_input",
        )
        if st.button("🤖 クロール & 登録"):
            if crawl_url_input.startswith("http"):
                with st.spinner("クロール中…"):
                    # ★INTEGRATION POINT: crawler.py + database.py + ranking.py
                    result = do_crawl_and_register(crawl_url_input)
                if result.get("crawl_status") == "success":
                    st.success(f"✅ 登録完了: {result.get('title','')}")
                else:
                    st.error("❌ クロール失敗")
            else:
                st.warning("https:// から始まるURLを入力してください")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:16px 48px 0;">', unsafe_allow_html=True)
    if st.button("← 事業案一覧に戻る"):
        st.session_state.step = "idea_list"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# メイン描画
# ─────────────────────────────────────────────────────────────────────────────
render_navbar()

step = st.session_state.step
if   step == "landing":    render_landing()
elif step == "issue_list": render_issue_list()
elif step == "idea_list":  render_idea_list()
elif step == "detail":     render_detail()

st.markdown("""
<div class="footer">
    © 2025 PROJECT ZERO — BizSpark AI × IdeaForge · Tech0 Search v2.0<br>
    Powered by Gemini AI · TF-IDF · SQLite · Streamlit
</div>
""", unsafe_allow_html=True)
