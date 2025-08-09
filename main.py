"""
このファイルは、Webアプリのメイン処理が記述されたファイルです。
"""

############################################################
# 1. ライブラリの読み込み
############################################################
from dotenv import load_dotenv
import logging
import streamlit as st
import utils
from initialize import initialize
import components as cn
import constants as ct


############################################################
# 2. 設定関連
############################################################
st.set_page_config(page_title=ct.APP_NAME, layout="wide")

# set_page_config の後・columns の前で一度だけ
st.markdown("""
<style>
/* 右カラム全体（タイトル側） */
.block-container {
    padding-top: 2rem !important;  /* 上余白を揃えるために追加 */
    padding-bottom: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
}

/* 左カラム全体をグレーにして高さ100% */
div[data-testid="stHorizontalBlock"] > div:first-child {
    background-color: #f3f3f3 !important;
    padding: 16px !important;
    margin: 0 !important;
    height: 100vh !important;
    padding-top: 2rem !important;  /* 右と同じ高さにする */
}
</style>
""", unsafe_allow_html=True)






logger = logging.getLogger(ct.LOGGER_NAME)


############################################################
# 3. 初期化処理
############################################################
try:
    initialize()
except Exception as e:
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    st.stop()

if not "initialized" in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)


############################################################
# 4. 初期表示
############################################################


# ===== 2カラムレイアウト =====
left, right = st.columns([2.5, 7.5])
with left:
    cn.display_select_mode(show_header=False)
    cn.display_examples_block()


with right:
    cn.display_app_title()
    cn.display_initial_ai_message()
    with st.form("chat_form", clear_on_submit=True):
        user_text = st.text_area("メッセージを入力", height=80, placeholder="こちらに入力してください。")
        submitted = st.form_submit_button("送信")


############################################################
# 5. 会話ログの表示
############################################################
try:
    with right:
        try:
            cn.display_conversation_log()
        except Exception as e:
            logger.error(f"{ct.CONVERSATION_LOG_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.CONVERSATION_LOG_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            st.stop()
except Exception as e:
    logger.error(f"{ct.CONVERSATION_LOG_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.CONVERSATION_LOG_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    st.stop()


############################################################
# 6. チャット入力の受け付け
############################################################
chat_message = None
if submitted and user_text and user_text.strip():
    chat_message = user_text.strip()


############################################################
# 7. チャット送信時の処理
############################################################
if chat_message:
    logger.info({"message": chat_message, "application_mode": st.session_state.mode})

    with right:
        with st.chat_message("user"):
            st.markdown(chat_message)

        res_box = st.empty()
        with st.spinner(ct.SPINNER_TEXT):
            try:
                llm_response = utils.get_llm_response(chat_message)
            except Exception as e:
                logger.error(f"{ct.GET_LLM_RESPONSE_ERROR_MESSAGE}\n{e}")
                st.error(utils.build_error_message(ct.GET_LLM_RESPONSE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
                st.stop()

        try:
            with st.chat_message("assistant"):
                if st.session_state.mode == ct.ANSWER_MODE_1:
                    content = cn.display_search_llm_response(llm_response)
                else:
                    content = cn.display_contact_llm_response(llm_response)

            logger.info({"message": content, "application_mode": st.session_state.mode})
        except Exception as e:
            logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            st.stop()

    st.session_state.messages.append({"role": "user", "content": chat_message})
    st.session_state.messages.append({"role": "assistant", "content": content})
