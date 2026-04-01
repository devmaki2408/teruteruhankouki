import streamlit as st
import openai_client as ai


# ---------------------------
# ページ設定
# ---------------------------
st.set_page_config(
    page_title="BizSpark AI",
    page_icon="⚡",
    layout="wide",
)


# ---------------------------
# 簡易CSS
# ---------------------------
CUSTOM_CSS = """
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }
    .sub-copy {
        color: #666;
        margin-bottom: 1.5rem;
    }
    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }
    .card {
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        background: #FFFFFF;
    }
    .mini-card {
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 14px;
        background: #FFFFFF;
        height: 100%;
    }
    .pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: #EEF2FF;
        color: #3730A3;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .score-box {
        display: inline-block;
        padding: 8px 14px;
        border-radius: 999px;
        background: #EFF6FF;
        color: #1D4ED8;
        font-weight: 700;
    }
    .force-label {
        font-weight: 700;
        margin-bottom: 6px;
    }
    .muted {
        color: #6B7280;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------
# モックデータ
# ---------------------------
MOCK_ISSUES = [
    {
        "title": "育児と仕事の両立による時間不足",
        "description": "保育園の送迎、家事、仕事が重なり、自分や家族のために使える時間が不足している。",
    },
    {
        "title": "育児情報の分散と信頼性の低さ",
        "description": "SNSやネット記事、病院など情報源が分かれており、何を信じるべきか判断が難しい。",
    },
    {
        "title": "急な残業や体調不良時の預け先不足",
        "description": "緊急時に子どもを安心して預けられる先が見つからず、仕事との両立が不安定になる。",
    },
    {
        "title": "夫婦間での育児負担の偏り",
        "description": "役割分担が曖昧で、片方に家事・育児が集中しやすく、関係性にも影響が出る。",
    },
    {
        "title": "子どもの教育投資の判断が難しい",
        "description": "習い事や教材が多く、何が子どもに合うのかを判断する材料が不足している。",
    },
]

MOCK_IDEAS = [
    {
        "title": "AI育児アシスタントSaaS",
        "overview": "家庭状況や子どもの発達記録をもとに、日々の育児判断を支援するAIサービス。",
        "solution": "発達記録・生活リズム・保護者の悩みを入力し、AIが優先課題と対応策を提案する。",
        "value": "迷いを減らし、育児判断の時間を短縮できる。",
        "score": 91,
        "reason": "課題適合度と継続利用のしやすさが高く、将来的な周辺サービス展開もしやすい。",
    },
    {
        "title": "共働き家庭向け緊急サポートマッチング",
        "overview": "急な残業や体調不良時に、近隣や提携先の支援リソースとつながれる仕組み。",
        "solution": "位置情報と条件登録をもとに、短時間で利用可能な預け先・送迎支援を提示する。",
        "value": "緊急時の不安を減らし、仕事継続性を高める。",
        "score": 84,
        "reason": "課題は強いが、オペレーション設計と信頼確保が成功の鍵になる。",
    },
    {
        "title": "育児ナレッジ統合プラットフォーム",
        "overview": "分散した育児情報を整理し、家庭ごとに必要な情報だけを届ける仕組み。",
        "solution": "複数情報源を整理し、家庭の属性に応じて優先度付きで見せる。",
        "value": "情報収集の負担を減らし、納得感のある意思決定を支援できる。",
        "score": 78,
        "reason": "ニーズは大きいが、差別化と継続利用設計が必要。",
    },
]

MOCK_FIVE_FORCES = {
    "five_forces": {
        "industry_rivalry": {
            "score": 4,
            "reason": "既存の育児アプリや情報サービスが多く、差別化が必要。",
        },
        "threat_of_new_entry": {
            "score": 3,
            "reason": "技術参入は可能だが、信頼性と継続利用の設計が参入障壁になる。",
        },
        "threat_of_substitutes": {
            "score": 3,
            "reason": "紙の記録、SNS、既存検索などで一部代替できる。",
        },
        "buyer_power": {
            "score": 4,
            "reason": "ユーザーは代替手段を持ちやすく、比較検討もしやすい。",
        },
        "supplier_power": {
            "score": 2,
            "reason": "サービス構築に必要な外部依存は相対的に限定的。",
        },
    }
}

MOCK_MEMBERS = [
    {
        "name": "田中 健一",
        "skills": ["新規事業開発", "PM"],
        "reason": "新規事業立ち上げとプロジェクト推進の経験があり、全体設計に向いている。",
    },
    {
        "name": "佐藤 美咲",
        "skills": ["UXリサーチ", "UI/UX設計"],
        "reason": "ユーザー理解と体験設計に強く、課題適合性の高いサービスに落とし込める。",
    },
    {
        "name": "鈴木 翔太",
        "skills": ["法人営業", "アライアンス"],
        "reason": "提携先開拓や外部連携に強く、事業拡大の初期フェーズを支えられる。",
    },
    {
        "name": "高橋 結衣",
        "skills": ["技術選定", "インフラ"],
        "reason": "安定したシステム基盤を設計でき、プロダクト初期構築の実現性を高められる。",
    },
]


# ---------------------------
# セッション初期化
# ---------------------------
def init_session() -> None:
    defaults = {
        "step": "input",
        "target": "",
        "issues": [],
        "selected_issue": None,
        "ideas": [],
        "selected_idea": None,
        "five_forces": None,
        "member_cards": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session()


# ---------------------------
# AI / モック橋渡し
# ---------------------------
def get_issues(target: str):
    result = ai.fetch_issues_from_ai(target)
    if result and "issues" in result and result["issues"]:
        return result["issues"]
    return MOCK_ISSUES


def get_more_issues(target: str, existing_issues):
    result = ai.fetch_more_issues_from_ai(target, existing_issues)
    if result and "issues" in result and result["issues"]:
        return result["issues"]
    return []


def get_ideas(target: str, issue_title: str, issue_description: str):
    result = ai.fetch_ideas_from_ai(target, issue_title, issue_description)
    if result and "ideas" in result and result["ideas"]:
        return result["ideas"]
    return MOCK_IDEAS


def get_more_ideas(target: str, issue_title: str, issue_description: str, existing_ideas):
    result = ai.fetch_more_ideas_from_ai(target, issue_title, issue_description, existing_ideas)
    if result and "ideas" in result and result["ideas"]:
        return result["ideas"]
    return []


def get_five_forces(idea_title: str, idea_overview: str):
    result = ai.fetch_five_forces_from_ai(idea_title, idea_overview)
    if result and "five_forces" in result:
        return result
    return MOCK_FIVE_FORCES


def get_member_cards(idea_title: str):
    cards = []
    for member in MOCK_MEMBERS:
        ai_result = ai.fetch_member_reason_from_ai(
            idea_title,
            member["name"],
            member["skills"],
        )
        reason = member["reason"]
        if ai_result and "member_reason" in ai_result:
            reason = ai_result["member_reason"].get("reason", reason)

        cards.append(
            {
                "name": member["name"],
                "skills": member["skills"],
                "reason": reason,
            }
        )
    return cards


# ---------------------------
# レンダリング関数
# ---------------------------
def render_input() -> None:
    st.markdown('<div class="main-title">BizSpark AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-copy">ターゲットを入力すると、課題抽出から事業案比較まで行います。</div>',
        unsafe_allow_html=True,
    )

    target = st.text_input("ターゲットを入力してください", placeholder="例：30代共働き、子どもあり、都内在住")

    if st.button("課題を生成", use_container_width=True):
        if not target.strip():
            st.warning("ターゲットを入力してください。")
            return

        st.session_state.target = target.strip()
        with st.spinner("課題を生成しています..."):
            st.session_state.issues = get_issues(st.session_state.target)
        st.session_state.step = "issues"
        st.rerun()


def render_issues() -> None:
    st.markdown('<div class="section-title">課題一覧</div>', unsafe_allow_html=True)
    st.caption(f"ターゲット: {st.session_state.target}")

    for i, issue in enumerate(st.session_state.issues):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"### {issue['title']}")
        st.write(issue["description"])
        if st.button("この課題で事業案を生成", key=f"issue_select_{i}", use_container_width=True):
            st.session_state.selected_issue = issue
            with st.spinner("事業案を生成しています..."):
                st.session_state.ideas = get_ideas(
                    st.session_state.target,
                    issue["title"],
                    issue["description"],
                )
            st.session_state.step = "ideas"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("さらに5件生成", use_container_width=True):
            with st.spinner("追加の課題を生成しています..."):
                more = get_more_issues(st.session_state.target, st.session_state.issues)
            if more:
                st.session_state.issues.extend(more)
            else:
                st.info("追加の課題を生成できませんでした。")
            st.rerun()
    with col2:
        if st.button("最初に戻る", use_container_width=True):
            st.session_state.step = "input"
            st.rerun()


def render_ideas() -> None:
    st.markdown('<div class="section-title">事業案一覧</div>', unsafe_allow_html=True)
    issue = st.session_state.selected_issue
    st.caption(f"ターゲット: {st.session_state.target} / 課題: {issue['title']}")

    for i, idea in enumerate(st.session_state.ideas):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="pill">事業案</div>', unsafe_allow_html=True)
        st.markdown(f"### {idea['title']}")
        st.write(idea.get("overview", ""))

        if idea.get("solution"):
            st.write(f"**解決方法**: {idea['solution']}")
        if idea.get("value"):
            st.write(f"**提供価値**: {idea['value']}")
        if idea.get("score") is not None:
            st.markdown(
                f'<div class="score-box">スコア: {idea.get("score", 0)}</div>',
                unsafe_allow_html=True,
            )
        if idea.get("reason"):
            st.write(f"**理由**: {idea['reason']}")

        if st.button("この事業案の詳細を見る", key=f"idea_select_{i}", use_container_width=True):
            st.session_state.selected_idea = idea
            with st.spinner("分析結果を生成しています..."):
                st.session_state.five_forces = get_five_forces(
                    idea["title"],
                    idea.get("overview", ""),
                )
                st.session_state.member_cards = get_member_cards(idea["title"])
            st.session_state.step = "detail"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("さらに5件生成", use_container_width=True):
            with st.spinner("追加の事業案を生成しています..."):
                more = get_more_ideas(
                    st.session_state.target,
                    issue["title"],
                    issue["description"],
                    st.session_state.ideas,
                )
            if more:
                st.session_state.ideas.extend(more)
            else:
                st.info("追加の事業案を生成できませんでした。")
            st.rerun()
    with col2:
        if st.button("課題一覧に戻る", use_container_width=True):
            st.session_state.step = "issues"
            st.rerun()


def render_detail() -> None:
    idea = st.session_state.selected_idea
    ff = (st.session_state.five_forces or MOCK_FIVE_FORCES).get("five_forces", {})
    members = st.session_state.member_cards or MOCK_MEMBERS

    st.markdown('<div class="section-title">事業案詳細</div>', unsafe_allow_html=True)
    st.caption(f"ターゲット: {st.session_state.target}")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"### {idea['title']}")
    st.write(f"**概要**: {idea.get('overview', '')}")
    st.write(f"**解決方法**: {idea.get('solution', '')}")
    st.write(f"**提供価値**: {idea.get('value', '')}")
    st.markdown(
        f'<div class="score-box">スコア: {idea.get("score", 0)}</div>',
        unsafe_allow_html=True,
    )
    st.write(f"**スコア理由**: {idea.get('reason', '')}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">5Forces分析</div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    force_map = [
        ("industry_rivalry", "競争環境"),
        ("threat_of_new_entry", "新規参入"),
        ("threat_of_substitutes", "代替品"),
        ("buyer_power", "買い手交渉力"),
        ("supplier_power", "売り手交渉力"),
    ]
    cols = [col1, col2, col3, col4, col5]

    for col, (key, label) in zip(cols, force_map):
        item = ff.get(key, {"score": "-", "reason": "情報なし"})
        with col:
            st.markdown('<div class="mini-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="force-label">{label}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="score-box">{item.get("score", "-")}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"<div class='muted' style='margin-top:10px;'>{item.get('reason', '')}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">推奨人材</div>', unsafe_allow_html=True)
    member_cols = st.columns(4)
    for col, member in zip(member_cols, members):
        with col:
            st.markdown('<div class="mini-card">', unsafe_allow_html=True)
            st.markdown(f"### {member['name']}")
            st.write("**スキル**: " + " / ".join(member.get("skills", [])))
            st.write("**選定理由**: " + member.get("reason", ""))
            st.markdown('</div>', unsafe_allow_html=True)

    if st.button("事業案一覧に戻る", use_container_width=True):
        st.session_state.step = "ideas"
        st.rerun()


# ---------------------------
# メイン描画
# ---------------------------
if st.session_state.step == "input":
    render_input()
elif st.session_state.step == "issues":
    render_issues()
elif st.session_state.step == "ideas":
    render_ideas()
elif st.session_state.step == "detail":
    render_detail()