# app.py
# ============================================================
# 画面表示・画面遷移・全体制御
# ============================================================

import streamlit as st

import database as db
import openai_client as ai
import prompts
from ranking import deduplicate, rank_by_query


# ============================================================
# モックデータ
# ============================================================

MOCK_ISSUES = [
    {"id": 1, "text": "高齢者の孤独・孤立問題が深刻化しており、日常的なコミュニケーション手段が不足している"},
    {"id": 2, "text": "介護施設スタッフの慢性的な人手不足により、個別ケアの質が低下している"},
    {"id": 3, "text": "認知症の早期発見が遅れ、適切な介入タイミングを逃すケースが多い"},
    {"id": 4, "text": "遠方に住む家族が親の健康状態をリアルタイムで把握する手段がない"},
    {"id": 5, "text": "地域包括支援センターへの相談窓口が少なく、情報へのアクセスに格差がある"},
]
MOCK_MORE_ISSUES = [
    {"id": 6, "text": "リハビリの継続率が低く、退院後の機能回復が進まない"},
    {"id": 7, "text": "服薬管理が難しく、誤薬・飲み忘れによる健康被害が発生している"},
    {"id": 8, "text": "介護保険制度の複雑さにより、利用できるサービスを知らない高齢者が多い"},
    {"id": 9, "text": "介護者（家族）のメンタルヘルスケアが十分に行われていない"},
    {"id": 10, "text": "施設入居待機者が多く、在宅介護の限界を超えた家族が困窮している"},
]
MOCK_IDEAS = [
    {"id": 1, "title": "AIコンシェルジュ話し相手サービス",
     "summary": "高齢者向けに毎日自動でコールし、会話・健康チェック・服薬確認を行うAIエージェント。", "score": 82},
    {"id": 2, "title": "介護スタッフ業務自動化プラットフォーム",
     "summary": "記録・シフト・申し送りをAIで自動化し、スタッフの直接ケア時間を最大化するSaaS。", "score": 78},
    {"id": 3, "title": "認知症早期スクリーニングアプリ",
     "summary": "スマホの操作ログ・音声から認知機能の変化を継続モニタリングし、家族・医師へ通知。", "score": 75},
    {"id": 4, "title": "遠距離家族向け見守りダッシュボード",
     "summary": "センサー・ウェアラブル・訪問記録を統合し、離れた家族がワンビューで状態把握できるサービス。", "score": 71},
    {"id": 5, "title": "地域ケアナビゲーターマッチング",
     "summary": "地域の支援制度・施設情報をパーソナライズして提供し、ケアマネジャーとのマッチングも行うプラットフォーム。", "score": 68},
]
MOCK_MORE_IDEAS = [
    {"id": 6, "title": "リハビリ継続支援アプリ",
     "summary": "動画ガイド・進捗可視化・リマインダーで在宅リハビリの継続率を向上させるアプリ。", "score": 65},
    {"id": 7, "title": "スマート服薬管理デバイス",
     "summary": "IoT薬箱＋アプリで飲み忘れ・誤薬を防止し、薬局・医師と情報共有できるデバイスサービス。", "score": 63},
    {"id": 8, "title": "介護保険ナビAI",
     "summary": "利用者の状況をヒアリングして最適な介護保険サービスを提案するチャットボット。", "score": 60},
    {"id": 9, "title": "介護者メンタルケアコミュニティ",
     "summary": "介護家族向けのオンラインコミュニティ＋専門家相談窓口をサブスクで提供。", "score": 57},
    {"id": 10, "title": "施設入居マッチングプラットフォーム",
     "summary": "空き状況・価格・評判をリアルタイム集約し、最短で最適施設を探せるマッチングサービス。", "score": 54},
]
MOCK_DETAIL = {
    "five_forces": {
        "競合（既存競合との競争）": "大手通信会社・ヘルスケアスタートアップが参入済み。ただし高齢者特化×AIコンシェルジュの専業プレイヤーは少なく差別化余地あり。",
        "新規参入の脅威": "初期開発コストは中程度。SaaS型で規模化しやすいが、医療・個人情報規制がバリアとなる。",
        "代替品の脅威": "家族による電話・訪問介護サービスが代替。ただし費用・手間のトレードオフで本サービスへのニーズは高い。",
        "買い手の交渉力": "個人高齢者は価格感度が高い。自治体・施設向けB2Bモデルへの転換で交渉力を分散できる。",
        "売り手の交渉力": "AIモデルはAPIで調達可能。音声認識・TTS技術の依存度は高いが複数ベンダー選択肢あり。",
    },
    "talent": [
        {"role": "AIエンジニア（音声・NLP）",
         "reason": "自然な会話生成と音声認識の品質が製品体験の核心。LLMファインチューニング・音声合成の実装経験が必須。"},
        {"role": "ケアマネジャー経験者（ドメインアドバイザー）",
         "reason": "高齢者・家族・施設の実態を深く理解した人材が、ユースケース設計と規制対応の両面で不可欠。"},
        {"role": "BizDev（自治体・医療機関営業）",
         "reason": "公的機関・介護施設へのエンタープライズ営業は関係構築に時間がかかる。早期からの専任人材が成長速度を左右する。"},
        {"role": "プロダクトデザイナー（高齢者UX専門）",
         "reason": "デジタルリテラシーが多様な高齢者向けUIは専門知識が必要。誤操作・離脱率の最小化が継続率に直結する。"},
    ],
}

STEPS = ["ターゲット入力", "課題選択", "事業案選択", "詳細分析"]
PAGE_TO_STEP = {"landing": 0, "issue_list": 1, "idea_list": 2, "detail": 3}


# ============================================================
# カスタムCSS
# ============================================================

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', 'Inter', sans-serif;
    }
    .stApp {
        background: #0f1117;
        color: #e2e8f0;
    }
    .block-container {
        max-width: 820px !important;
        padding: 2rem 2rem 5rem !important;
    }
    header[data-testid="stHeader"] { display: none; }
    #MainMenu { display: none; }
    footer { display: none; }

    .step-bar {
        display: flex;
        align-items: center;
        background: #1a1d27;
        border: 1px solid #2a2d3e;
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 2.4rem;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
        min-width: 0;
    }
    .step-dot {
        width: 26px; height: 26px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 700;
        flex-shrink: 0;
        border: 2px solid #2a2d3e;
        background: transparent;
        color: #4b5563;
    }
    .step-dot.active {
        background: linear-gradient(135deg,#6366f1,#8b5cf6);
        border-color: transparent; color: #fff;
        box-shadow: 0 0 14px rgba(99,102,241,.5);
    }
    .step-dot.done {
        background: #10b981; border-color: transparent; color: #fff;
    }
    .step-label {
        font-size: 11px; font-weight: 500;
        color: #4b5563; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis;
    }
    .step-label.active { color: #a5b4fc; }
    .step-label.done   { color: #6ee7b7; }
    .step-line {
        flex: 0 0 20px; height: 1px;
        background: #2a2d3e; margin: 0 4px;
    }
    .step-line.done { background: #10b981; }

    .hero-wrap { text-align: center; padding: 2.5rem 0 2rem; }
    .hero-badge {
        display: inline-block;
        background: rgba(99,102,241,.12);
        border: 1px solid rgba(99,102,241,.3);
        color: #a5b4fc; font-size: 11px; font-weight: 700;
        padding: 4px 14px; border-radius: 100px; letter-spacing: 1px;
        margin-bottom: 1.2rem;
    }
    .hero-title {
        font-size: 36px; font-weight: 800; line-height: 1.25;
        letter-spacing: -0.5px; margin-bottom: 1rem;
        background: linear-gradient(135deg, #f1f5f9 0%, #a5b4fc 55%, #8b5cf6 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-desc {
        font-size: 14px; color: #94a3b8; line-height: 1.75; margin-bottom: 2.2rem;
    }

    .page-title {
        font-size: 24px; font-weight: 800; color: #f1f5f9;
        margin-bottom: 4px; letter-spacing: -0.3px;
    }
    .page-subtitle {
        font-size: 13px; color: #64748b; margin-bottom: 1.4rem;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }

    .stTextArea textarea {
        background: #1a1d27 !important;
        border: 1px solid #2a2d3e !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-size: 14px !important;
        font-family: 'Noto Sans JP', sans-serif !important;
        padding: 14px !important;
        resize: none !important;
    }
    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,.15) !important;
        outline: none !important;
    }
    .stTextInput > div > div > input {
        background: #1a1d27 !important;
        border: 1px solid #2a2d3e !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        font-size: 13px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,.15) !important;
    }

    div.stButton > button {
        background: #1a1d27 !important;
        border: 1px solid #2a2d3e !important;
        color: #94a3b8 !important;
        font-size: 13px !important; font-weight: 500 !important;
        border-radius: 8px !important;
        padding: 0.55rem 1rem !important;
        transition: all 0.18s !important;
    }
    div.stButton > button:hover {
        border-color: #6366f1 !important;
        color: #a5b4fc !important;
        background: rgba(99,102,241,.08) !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg,#6366f1,#8b5cf6) !important;
        border: none !important;
        color: #fff !important;
        font-weight: 600 !important;
    }
    div.stButton > button[kind="primary"]:hover {
        opacity: .88 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px rgba(99,102,241,.4) !important;
    }

    .issue-card {
        background: #1a1d27;
        border: 1px solid #2a2d3e;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 8px;
        display: flex; align-items: flex-start; gap: 12px;
        transition: border-color .18s, background .18s;
        cursor: pointer;
    }
    .issue-card.selected {
        border-color: #6366f1;
        background: rgba(99,102,241,.07);
    }
    .issue-num {
        font-size: 10px; font-weight: 700; color: #6366f1;
        background: rgba(99,102,241,.13);
        border-radius: 4px; padding: 3px 7px;
        flex-shrink: 0; margin-top: 1px; letter-spacing: .5px;
    }
    .issue-text { font-size: 13.5px; line-height: 1.65; color: #cbd5e1; flex: 1; }
    .issue-check { color: #6366f1; font-size: 15px; flex-shrink: 0; margin-top: 1px; }

    .idea-card {
        background: #1a1d27;
        border: 1px solid #2a2d3e;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 10px;
        position: relative; overflow: hidden;
        transition: border-color .18s, transform .15s;
    }
    .idea-card::before {
        content: '';
        position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
        background: linear-gradient(180deg,#6366f1,#8b5cf6);
        opacity: 0; transition: opacity .18s;
    }
    .idea-card.selected { border-color: #6366f1; background: rgba(99,102,241,.07); }
    .idea-card.selected::before { opacity: 1; }
    .idea-header {
        display: flex; align-items: flex-start;
        justify-content: space-between; gap: 12px; margin-bottom: 8px;
    }
    .idea-title { font-size: 15px; font-weight: 700; color: #f1f5f9; }
    .idea-score {
        background: rgba(99,102,241,.18);
        border: 1px solid rgba(99,102,241,.28);
        color: #a5b4fc; font-size: 12px; font-weight: 700;
        padding: 3px 11px; border-radius: 100px; white-space: nowrap; flex-shrink: 0;
    }
    .idea-summary { font-size: 13px; color: #94a3b8; line-height: 1.65; }

    .detail-hero {
        background: linear-gradient(135deg,#1a1d27,#1c1830);
        border: 1px solid #2a2d3e;
        border-radius: 14px; padding: 24px 26px; margin-bottom: 1.6rem;
    }
    .detail-title { font-size: 21px; font-weight: 800; color: #f1f5f9; margin-bottom: 8px; }
    .detail-summary { font-size: 13.5px; color: #94a3b8; line-height: 1.7; margin-bottom: 18px; }
    .score-pill {
        display: inline-flex; align-items: baseline; gap: 6px;
        background: rgba(99,102,241,.14);
        border: 1px solid rgba(99,102,241,.28);
        border-radius: 8px; padding: 8px 18px;
    }
    .score-label { font-size: 11px; font-weight: 600; color: #6366f1; }
    .score-value { font-size: 26px; font-weight: 800; color: #a5b4fc; }

    .section-heading {
        font-size: 14px; font-weight: 700; color: #e2e8f0;
        display: flex; align-items: center; gap: 8px;
        margin: 1.8rem 0 1rem;
        padding-bottom: 10px; border-bottom: 1px solid #2a2d3e;
    }

    .force-card {
        background: #1a1d27; border: 1px solid #2a2d3e;
        border-radius: 9px; padding: 14px 16px; margin-bottom: 8px;
    }
    .force-label {
        font-size: 10px; font-weight: 700; color: #6366f1;
        text-transform: uppercase; letter-spacing: .8px; margin-bottom: 5px;
    }
    .force-text { font-size: 13px; color: #94a3b8; line-height: 1.65; }

    .talent-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }
    .talent-card {
        background: #1a1d27; border: 1px solid #2a2d3e;
        border-radius: 9px; padding: 14px 16px;
    }
    .talent-role { font-size: 13px; font-weight: 700; color: #f1f5f9; margin-bottom: 5px; }
    .talent-reason { font-size: 12px; color: #94a3b8; line-height: 1.6; }

    .api-live {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(16,185,129,.1); border: 1px solid rgba(16,185,129,.28);
        color: #6ee7b7; font-size: 11px; font-weight: 600;
        padding: 4px 12px; border-radius: 100px; margin-bottom: 1.4rem;
    }
    .api-demo {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(245,158,11,.1); border: 1px solid rgba(245,158,11,.28);
        color: #fcd34d; font-size: 11px; font-weight: 600;
        padding: 4px 12px; border-radius: 100px; margin-bottom: 1.4rem;
    }
    .dot-g { width:7px;height:7px;border-radius:50%;background:#10b981;animation:blink 2s infinite; }
    .dot-y { width:7px;height:7px;border-radius:50%;background:#f59e0b; }
    @keyframes blink { 0%,100%{opacity:1}50%{opacity:.35} }

    hr { border-color: #2a2d3e !important; margin: 1.4rem 0 !important; }
    label { color: #94a3b8 !important; font-size: 12px !important; }
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0f1117; }
    ::-webkit-scrollbar-thumb { background: #2a2d3e; border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# UIヘルパー
# ============================================================

def render_step_bar(current_page: str):
    step = PAGE_TO_STEP.get(current_page, 0)
    html = '<div class="step-bar">'
    for i, label in enumerate(STEPS):
        if i < step:
            dc, lc, inner = "done", "done", "✓"
        elif i == step:
            dc, lc, inner = "active", "active", str(i + 1)
        else:
            dc, lc, inner = "", "", str(i + 1)
        html += f'<div class="step-item"><div class="step-dot {dc}">{inner}</div><span class="step-label {lc}">{label}</span></div>'
        if i < len(STEPS) - 1:
            lc2 = "done" if i < step else ""
            html += f'<div class="step-line {lc2}"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def ai_ready(*required_funcs: str) -> bool:
    is_available = getattr(ai, "is_available", None)
    if not callable(is_available):
        return False

    try:
        if not is_available():
            return False
    except Exception:
        return False

    for func_name in required_funcs:
        func = getattr(ai, func_name, None)
        if not callable(func):
            return False

    return True


def api_badge():
    if ai_ready():
        st.markdown('<span class="api-live"><span class="dot-g"></span>OpenAI API 接続済み</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="api-demo"><span class="dot-y"></span>デモモード（OPENAI_API_KEY 未設定 または openai_client 未対応）</span>', unsafe_allow_html=True)


# ============================================================
# セッション初期化
# ============================================================

def init_session():
    defaults = {
        "page": "landing",
        "target": "",
        "session_id": None,
        "issues": [],
        "selected_issue": None,
        "ideas": [],
        "selected_idea": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ============================================================
# データ取得
# ============================================================

def fetch_issues(target: str) -> list:
    if ai_ready("call_openai", "parse_json_response"):
        prompt = prompts.build_issue_prompt(target)
        parsed = ai.parse_json_response(ai.call_openai(prompt))
        if isinstance(parsed, list) and parsed:
            issues = [{"id": i + 1, "text": item.get("text", "")} for i, item in enumerate(parsed)]
            sid = db.create_session(target)
            st.session_state.session_id = sid
            for issue, did in zip(issues, db.save_issues(sid, issues)):
                issue["db_id"] = did
            return issues
    return MOCK_ISSUES.copy()


def fetch_more_issues(target: str, existing: list) -> list:
    if ai_ready("call_openai", "parse_json_response"):
        prompt = prompts.build_more_issue_prompt(target, [i["text"] for i in existing])
        parsed = ai.parse_json_response(ai.call_openai(prompt))
        if isinstance(parsed, list) and parsed:
            sid = max(i["id"] for i in existing) + 1
            more = [{"id": sid + i, "text": item.get("text", "")} for i, item in enumerate(parsed)]
            if st.session_state.session_id:
                for issue, did in zip(more, db.save_issues(st.session_state.session_id, more)):
                    issue["db_id"] = did
            return deduplicate(existing + more, text_key="text")
    return MOCK_MORE_ISSUES.copy()


def fetch_ideas(target: str, issue: dict) -> list:
    if ai_ready("call_openai", "parse_json_response"):
        prompt = prompts.build_idea_prompt(target, issue["text"])
        parsed = ai.parse_json_response(ai.call_openai(prompt))
        if isinstance(parsed, list) and parsed:
            ideas = [{"id": i + 1, "title": x.get("title", ""), "summary": x.get("summary", ""), "score": int(x.get("score", 50))} for i, x in enumerate(parsed)]
            if st.session_state.session_id and issue.get("db_id"):
                for idea, did in zip(ideas, db.save_ideas(st.session_state.session_id, issue["db_id"], ideas)):
                    idea["db_id"] = did
            return ideas
    return MOCK_IDEAS.copy()


def fetch_more_ideas(target: str, issue: dict, existing: list) -> list:
    if ai_ready("call_openai", "parse_json_response"):
        prompt = prompts.build_more_idea_prompt(target, issue["text"], [i["title"] for i in existing])
        parsed = ai.parse_json_response(ai.call_openai(prompt))
        if isinstance(parsed, list) and parsed:
            sid = max(i["id"] for i in existing) + 1
            more = [{"id": sid + i, "title": x.get("title", ""), "summary": x.get("summary", ""), "score": int(x.get("score", 50))} for i, x in enumerate(parsed)]
            if st.session_state.session_id and issue.get("db_id"):
                for idea, did in zip(more, db.save_ideas(st.session_state.session_id, issue["db_id"], more)):
                    idea["db_id"] = did
            return existing + more
    return MOCK_MORE_IDEAS.copy()


def fetch_detail(idea: dict) -> dict:
    if idea.get("db_id"):
        cached = db.get_detail(idea["db_id"])
        if cached:
            return cached
    if ai_ready("call_openai", "parse_json_response"):
        prompt = prompts.build_detail_prompt(idea["title"], idea["summary"])
        parsed = ai.parse_json_response(ai.call_openai(prompt, max_tokens=2000))
        if isinstance(parsed, dict) and "five_forces" in parsed:
            if idea.get("db_id"):
                db.save_detail(idea["db_id"], parsed)
            return parsed
    return MOCK_DETAIL.copy()


# ============================================================
# 画面レンダリング
# ============================================================

def render_landing():
    render_step_bar("landing")
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-badge">✦ AI BUSINESS ARCHITECT</div>
        <div class="hero-title">新規事業アイデアを<br>AIが体系的に設計する</div>
        <div class="hero-desc">ターゲットを入力するだけで、課題の抽出から事業案の生成、<br>5Forces分析・推奨人材まで一気通貫でアウトプットします。</div>
    </div>
    """, unsafe_allow_html=True)

    api_badge()

    target = st.text_area(
        "ターゲット",
        placeholder="例：一人暮らしの高齢者（70代）とその家族",
        height=110,
        label_visibility="collapsed",
    )
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("課題を生成する　→", type="primary", use_container_width=True):
        if not target.strip():
            st.warning("ターゲットを入力してください。")
            return
        with st.spinner("課題を分析中..."):
            issues = fetch_issues(target.strip())
        st.session_state.update(
            target=target.strip(), issues=issues,
            selected_issue=None, ideas=[], selected_idea=None, page="issue_list"
        )
        st.rerun()


def render_issue_list():
    render_step_bar("issue_list")
    st.markdown('<div class="page-title">課題一覧</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">ターゲット：{st.session_state.target}</div>', unsafe_allow_html=True)

    issues = st.session_state.issues
    selected_id = st.session_state.selected_issue

    query = st.text_input("絞り込み", placeholder="🔍 キーワードで絞り込み...", label_visibility="collapsed")
    display = rank_by_query(query.strip(), issues, text_key="text", top_n=len(issues)) if query.strip() else issues
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    for issue in display:
        sel = selected_id == issue["id"]
        check = '<span class="issue-check">✓</span>' if sel else ""
        cls = "issue-card selected" if sel else "issue-card"
        st.markdown(f"""
        <div class="{cls}">
            <span class="issue-num">#{issue['id']:02d}</span>
            <span class="issue-text">{issue['text']}</span>
            {check}
        </div>""", unsafe_allow_html=True)
        if st.button("選択", key=f"iss_{issue['id']}"):
            st.session_state.selected_issue = issue["id"]
            st.rerun()

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1.5])
    with c1:
        if st.button("← 戻る", use_container_width=True):
            st.session_state.page = "landing"; st.rerun()
    with c2:
        if st.button("さらに5件生成", use_container_width=True):
            with st.spinner("生成中..."):
                more = fetch_more_issues(st.session_state.target, issues)
            ex_ids = {i["id"] for i in issues}
            st.session_state.issues = issues + [i for i in more if i["id"] not in ex_ids]
            st.rerun()
    with c3:
        if st.button("事業案を生成する　→", type="primary", use_container_width=True):
            if selected_id is None:
                st.warning("課題を1件選択してください。"); return
            sel_issue = next(i for i in issues if i["id"] == selected_id)
            with st.spinner("事業案を生成中..."):
                ideas = fetch_ideas(st.session_state.target, sel_issue)
            st.session_state.update(ideas=ideas, selected_idea=None, page="idea_list")
            st.rerun()


def render_idea_list():
    render_step_bar("idea_list")
    sel_issue = next((i for i in st.session_state.issues if i["id"] == st.session_state.selected_issue), None)
    st.markdown('<div class="page-title">事業案一覧</div>', unsafe_allow_html=True)
    if sel_issue:
        st.markdown(f'<div class="page-subtitle">課題：{sel_issue["text"]}</div>', unsafe_allow_html=True)

    ideas = st.session_state.ideas
    selected_id = st.session_state.selected_idea

    query = st.text_input("絞り込み", placeholder="🔍 キーワードで絞り込み...", label_visibility="collapsed")
    display = rank_by_query(query.strip(), ideas, text_key="title", top_n=len(ideas)) if query.strip() else ideas
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    for idea in display:
        sel = selected_id == idea["id"]
        cls = "idea-card selected" if sel else "idea-card"
        btn_label = "✓ 選択中" if sel else "選択する"
        st.markdown(f"""
        <div class="{cls}">
            <div class="idea-header">
                <span class="idea-title">{idea['title']}</span>
                <span class="idea-score">Score {idea['score']}</span>
            </div>
            <div class="idea-summary">{idea['summary']}</div>
        </div>""", unsafe_allow_html=True)
        if st.button(btn_label, key=f"idea_{idea['id']}"):
            st.session_state.selected_idea = idea["id"]; st.rerun()

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1.5])
    with c1:
        if st.button("← 戻る", use_container_width=True):
            st.session_state.page = "issue_list"; st.rerun()
    with c2:
        if st.button("さらに5件生成", use_container_width=True):
            with st.spinner("生成中..."):
                more = fetch_more_ideas(st.session_state.target, sel_issue, ideas)
            st.session_state.ideas = more; st.rerun()
    with c3:
        if st.button("詳細分析を見る　→", type="primary", use_container_width=True):
            if selected_id is None:
                st.warning("事業案を1件選択してください。"); return
            st.session_state.page = "detail"; st.rerun()


def render_detail():
    render_step_bar("detail")
    ideas = st.session_state.ideas
    idea = next((i for i in ideas if i["id"] == st.session_state.selected_idea), None)
    if idea is None:
        st.error("事業案が見つかりません。"); return

    with st.spinner("詳細を取得中..."):
        detail = fetch_detail(idea)

    st.markdown(f"""
    <div class="detail-hero">
        <div class="detail-title">{idea['title']}</div>
        <div class="detail-summary">{idea['summary']}</div>
        <div class="score-pill">
            <span class="score-label">総合スコア</span>
            <span class="score-value">{idea['score']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-heading">⬡ 5Forces 分析</div>', unsafe_allow_html=True)
    for force, text in detail["five_forces"].items():
        st.markdown(f"""
        <div class="force-card">
            <div class="force-label">{force}</div>
            <div class="force-text">{text}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-heading">◈ 推奨人材</div>', unsafe_allow_html=True)
    talent_html = "".join([
        f'<div class="talent-card"><div class="talent-role">👤 {p["role"]}</div><div class="talent-reason">{p["reason"]}</div></div>'
        for p in detail["talent"]
    ])
    st.markdown(f'<div class="talent-grid">{talent_html}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    if st.button("← 事業案一覧へ戻る"):
        st.session_state.page = "idea_list"; st.rerun()


# ============================================================
# メインルーター
# ============================================================

def main():
    st.set_page_config(
        page_title="AI Business Architect",
        page_icon="⬡",
        layout="centered",
    )
    inject_css()
    db.init_db()
    init_session()

    page = st.session_state.page
    if page == "landing":       render_landing()
    elif page == "issue_list":  render_issue_list()
    elif page == "idea_list":   render_idea_list()
    elif page == "detail":      render_detail()
    else:
        st.session_state.page = "landing"; st.rerun()


if __name__ == "__main__":
    main()