import asyncio
import logging

import streamlit as st

from main import GraChalleInterface

# ログ設定（必要に応じて）
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# タイトル
st.title("GraChalle: 会話式外国語試験Bot")

# 初期化
interface = GraChalleInterface()

# セッション状態（会話保持用）
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.language = None
    st.session_state.level = None
    st.session_state.conversation_turns = 0
    st.session_state.history = []

# ステップ1: 最初の入力受付
if not st.session_state.started:
    user_input = st.text_input("試験のリクエストを入力してください")

    if user_input:
        confirmation, language, level = interface._intent_extract(user_input)

        st.write(f"✅ {confirmation}")

        if language and level:
            st.session_state.language = language
            st.session_state.level = level
            st.session_state.started = True
        else:
            st.warning("試験に必要な情報が不足しています。入力を見直してください。")

# ステップ2: 会話モード
elif st.session_state.started and st.session_state.conversation_turns < 3:
    if st.session_state.conversation_turns == 0:

        async def init():
            return await interface.examination.initialize_conversation(
                st.session_state.language, st.session_state.level
            )

        init_message = asyncio.run(init())
        st.session_state.history.append(("試験官", init_message))
        st.session_state.conversation_turns += 1

    for role, msg in st.session_state.history:
        st.markdown(f"**{role}**: {msg}")

    user_reply = st.text_input("あなたの返答を入力してください", key="reply")

    if user_reply:

        async def continue_conv():
            return await interface.examination.continue_conversation(user_reply)

        bot_reply = asyncio.run(continue_conv())
        st.session_state.history.append(("あなた", user_reply))
        st.session_state.history.append(("試験官", bot_reply))
        st.session_state.conversation_turns += 1
        st.experimental_rerun()

# ステップ3: 評価モード
elif st.session_state.conversation_turns >= 3:

    async def evaluate():
        conv = interface.examination.get_conversation_history()
        return await interface._evaluator(conv)

    st.write("📝 評価中...")
    result = asyncio.run(evaluate())
    st.success("🎉 評価完了！")
    st.markdown(result)

    # リセットボタン
    if st.button("再試行"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.experimental_rerun()
