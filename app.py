import streamlit as st
import openai_client as ai

# ---------------------------
# セッション初期化
# ---------------------------
def init_session():
    if "step" not in st.session_state:
        st.session_state.step = "input"
    if "target" not in st.session_state:
        st.session_state.target = ""
    if "issues" not in st.session_state:
        st.session_state.issues = []
    if "ideas" not in st.session_state:
        st.session_state.ideas = []

init_session()

# ---------------------------
# 画面① ターゲット入力
# ---------------------------
def render_input():
    st.title("新規事業アイデア生成")

    target = st.text_input("ターゲットを入力してください")

    if st.button("課題を生成"):
        if target:
            st.session_state.target = target

            with st.spinner("課題生成中..."):
                result = ai.fetch_issues_from_ai(target)

            if result and "issues" in result:
                st.session_state.issues = result["issues"]
                st.session_state.step = "issues"
                st.rerun()
            else:
                st.error("課題生成に失敗しました")

# ---------------------------
# 画面② 課題一覧
# ---------------------------
def render_issues():
    st.title("課題一覧")

    for i, issue in enumerate(st.session_state.issues):
        st.markdown(f"### {issue['title']}")
        st.write(issue["description"])

        if st.button(f"この課題で事業案生成", key=f"issue_{i}"):
            with st.spinner("事業案生成中..."):
                result = ai.fetch_ideas_from_ai(
                    st.session_state.target,
                    issue["title"],
                    issue["description"],
                )

            if result and "ideas" in result:
                st.session_state.ideas = result["ideas"]
                st.session_state.step = "ideas"
                st.rerun()
            else:
                st.error("事業案生成に失敗しました")

    if st.button("戻る"):
        st.session_state.step = "input"
        st.rerun()

# ---------------------------
# 画面③ 事業案一覧
# ---------------------------
def render_ideas():
    st.title("事業案一覧")

    for i, idea in enumerate(st.session_state.ideas):
        st.markdown(f"### {idea['title']}")
        st.write(idea["overview"])

    if st.button("最初に戻る"):
        st.session_state.step = "input"
        st.rerun()

# ---------------------------
# メイン
# ---------------------------
if st.session_state.step == "input":
    render_input()

elif st.session_state.step == "issues":
    render_issues()

elif st.session_state.step == "ideas":
    render_ideas()