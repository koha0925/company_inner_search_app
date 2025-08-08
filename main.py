"""
このファイルは、Webアプリのメイン処理が記述されたファイルです。
"""

############################################################
# 1. ライブラリの読み込み
############################################################
# 「.env」ファイルから環境変数を読み込むための関数
from dotenv import load_dotenv
# ログ出力を行うためのモジュール
import logging
# streamlitアプリの表示を担当するモジュール
import streamlit as st
# （自作）画面表示以外の様々な関数が定義されているモジュール
import utils
# （自作）アプリ起動時に実行される初期化処理が記述された関数
from initialize import initialize
# （自作）画面表示系の関数が定義されているモジュール
import components as cn
# （自作）変数（定数）がまとめて定義・管理されているモジュール
import constants as ct


############################################################
# 2. 設定関連
############################################################
# ブラウザタブの表示文言を設定
st.set_page_config(
    page_title=ct.APP_NAME
)

# ログ出力を行うためのロガーの設定
logger = logging.getLogger(ct.LOGGER_NAME)


############################################################
# 3. 初期化処理
############################################################
try:
    # 初期化処理（「initialize.py」の「initialize」関数を実行）
    initialize()
except Exception as e:
    # エラーログの出力
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    # エラーメッセージの画面表示
    st.error(utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    # 後続の処理を中断
    st.stop()

# アプリ起動時のログファイルへの出力
if not "initialized" in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)


############################################################
# 4. 初期表示
############################################################
# ===== 2カラムレイアウト =====
left, right = st.columns([1, 2])

# ---- 左：モード選択 + 区切り + 例 ----
with left:
    cn.display_select_mode(container=left)  # ← 左カラムにラジオを出す（components.pyを置換済み前提）
    st.divider()
    cn.display_examples_block()            # ← 例ブロック（components.pyに追加した関数）

# ---- 右：タイトル + 案内文 ----
with right:
    cn.display_app_title()
    cn.display_initial_ai_message()



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
    # エラーログの出力
    logger.error(f"{ct.CONVERSATION_LOG_ERROR_MESSAGE}\n{e}")
    # エラーメッセージの画面表示
    st.error(utils.build_error_message(ct.CONVERSATION_LOG_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    # 後続の処理を中断
    st.stop()


############################################################
# 6. チャット入力の受け付け
############################################################
# 右カラムに入力フォームを追加（上の right カラムの続きに置く）
with right:
    with st.form("chat_form", clear_on_submit=True):
        user_text = st.text_area("メッセージを入力", height=80, placeholder="こちらに入力してください。")
        submitted = st.form_submit_button("送信")

# 既存フローに合わせるため、chat_message へ詰め替える
chat_message = None
if submitted and user_text and user_text.strip():
    chat_message = user_text.strip()



# ==========================================
# 7. チャット送信時の処理（右カラムに統一表示）
# ==========================================
if chat_message:
    # 7-1. ユーザーメッセージのログ出力
    logger.info({"message": chat_message, "application_mode": st.session_state.mode})

    with right:
        # 7-1. ユーザーメッセージの表示（右カラム）
        with st.chat_message("user"):
            st.markdown(chat_message)

        # 7-2. LLMからの回答取得（スピナー＋空プレースホルダでチラつき防止）
        res_box = st.empty()
        with st.spinner(ct.SPINNER_TEXT):
            try:
                llm_response = utils.get_llm_response(chat_message)
            except Exception as e:
                logger.error(f"{ct.GET_LLM_RESPONSE_ERROR_MESSAGE}\n{e}")
                st.error(utils.build_error_message(ct.GET_LLM_RESPONSE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
                st.stop()

        # 7-3. LLMからの回答表示（モード別）※右カラムに表示
        try:
            with st.chat_message("assistant"):
                if st.session_state.mode == ct.ANSWER_MODE_1:
                    content = cn.display_search_llm_response(llm_response)
                else:
                    content = cn.display_contact_llm_response(llm_response)

            # AIメッセージのログ出力
            logger.info({"message": content, "application_mode": st.session_state.mode})

        except Exception as e:
            logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            st.stop()

    # 7-4. 会話ログへの追加（画面再描画時のため）
    st.session_state.messages.append({"role": "user", "content": chat_message})
    st.session_state.messages.append({"role": "assistant", "content": content})
