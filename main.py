"""
このファイルは、Webアプリ（Streamlit）のメイン処理です。
画面レイアウト（左＝ナビ/例、右＝タイトル・案内・会話ログ・入力欄）と、
送信時のRAG応答表示までを担います。
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
# 2. 設定関連（ページ設定・共通スタイル）
############################################################
# タブタイトルと横幅レイアウトを設定
st.set_page_config(page_title=ct.APP_NAME, layout="wide")

# 画面共通のCSS（左右の余白・見た目の統一・UI微調整）
# 目的：
#  - 右カラムに左右パディングを入れて読みやすくする
#  - 左カラム全体をグレー地で包む（目的・入力例の領域）
#  - 小見出し・例ボックス・初期案内（緑）・注意（黄）などの見た目統一
#  - chat_input は通常レイアウト内の最下部に配置（固定はしない）
st.markdown("""
<style>
/* 右カラム全体（タイトル側）。上マージンを付けて左と高さ合わせ */
.block-container {
    padding-top: 2rem !important;  /* 上余白 */
    padding-bottom: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
}
/* 右カラムの左右に余白を追加（2列の2番目＝右カラム） */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
    padding-left: 5rem !important;
    padding-right: 5rem !important;
}
/* 左カラム全体をグレー背景に。高さは画面全体相当（100vh） */
div[data-testid="stHorizontalBlock"] > div:first-child {
    background-color: #f3f3f3 !important;
    padding: 16px !important;
    margin: 0 !important;
    height: 100vh !important;
    padding-top: 2rem !important;  /* 右と高さを揃える */
}
/* 左カラム：見出し（「利用目的」） */
.left-title{
    font-size:16px; font-weight:700; margin:0 0 8px 0;
}
/* 左カラム：小見出し（「◯◯を選択した場合」） */
.sec-title{
    font-weight:700; margin: 8px 0 6px 0; font-size: 14px;
}
/* 左カラム：入力例の白ボックス */
.example-box {
    background-color: white;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 14px;
    box-shadow: 0 0 0 1px rgba(0,0,0,0.05);
}
/* 右カラム：初期メッセージ（緑ボックス） */
.ai-message-box {
    background-color: #e8f5e9; /* 薄い緑背景 */
    color: #2e7d32;           /* 濃い緑文字 */
    padding: 20px;
    border-radius: 10px;
    font-size: 14px;
    line-height: 1.6;
    margin-bottom: 16px;      /* 黄色の注意ボックスとの間隔 */
}
/* st.warning（黄色の注意ボックス）をブランドに合わせて調整 */
div[data-testid="stNotification"] {
    background-color: #FFF8E1 !important; /* 薄い黄色 */
    border-radius: 8px !important;
    padding: 8px 12px !important;
}
div[data-testid="stNotification"] svg {
    fill: #c57c00 !important;            /* アイコン色 */
}
div[data-testid="stNotification"] p {
    color: #c57c00 !important;           /* テキスト色 */
    margin: 0 !important;
}
/* chat_input の上下余白（最下部に“自然に”配置する） */
div[data-testid="stChatInput"] {
    margin-top: 20px;     /* ログとの間隔 */
    margin-bottom: 40px;  /* 画面下との距離 */
}
</style>
""", unsafe_allow_html=True)

# ロガー取得（initialize() 内の設定により、以降の例外等がファイルに記録される）
logger = logging.getLogger(ct.LOGGER_NAME)


############################################################
# 3. 初期化処理（初回のみ）
############################################################
# 目的：
#  - セッションID生成（ログに紐づく）
#  - ログ設定（ファイル出力）
#  - Retriever 構築（ベクターストア作成＆検索器の用意）
try:
    initialize()
except Exception as e:
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    st.error(utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    st.stop()

# 初回起動ログ（2回目以降に重複出力されないよう session_state で制御）
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)


############################################################
# 4. 初期表示（レイアウトと静的セクション）
############################################################
# 二列レイアウト（左：ナビ/例　右：タイトル・案内・会話ログ・入力欄）
left, right = st.columns([2.5, 7.5])

# --- 左カラム：モード選択と使用例 ---
with left:
    # 「利用目的」見出し（ラジオ本体は components 側）
    st.markdown('<div class="left-title">利用目的</div>', unsafe_allow_html=True)

    # モード選択ラジオ（ラベルは隠し、外側見出しで説明）
    cn.display_select_mode(show_header=False)

    # 区切り線（Streamlit 組み込み。CSSの影響を受けづらく、手軽）
    st.divider()

    # 「社内文書検索」「社内問い合わせ」それぞれの説明と入力例（白ボックス）
    cn.display_examples_block()

# --- 右カラム：タイトル・初期案内・会話ログ・入力欄 ---
with right:
    # タイトル（ブラウザタブ名とは別に、画面上部の見出し）
    cn.display_app_title()

    # 初期のAIメッセージ（緑ボックス）＋ 注意（黄色ボックス）
    cn.display_initial_ai_message()

    # 👇 送受信メッセージを描画する“置き場”。
    # 　chat_input より前に定義することで、画面上では「入力欄の上」にログが並ぶ。
    messages_container = st.container()

    # 既存の会話ログ（セッション履歴）をまとめて再生。
    # これを消すと「送信直後のターンは見えるが、再実行時に過去ログが出ない」状態になる点に注意。
    with messages_container:
        cn.display_conversation_log()

    # 👇 入力欄はページ最下部（通常フロー）
    # 送信されると chat_message に文字列が入り、それ以外は None。
    chat_message = st.chat_input("こちらからメッセージを送信してください")


############################################################
# 5. （未使用）
#   ※ 以前は「会話ログの表示」をここでも行っていたが、二重描画になるため削除。
############################################################


############################################################
# 6. チャット入力の受け付け
#   - st.chat_input を使うため、submitted/user_text の詰め替えは不要。
############################################################
# ここでは何もしない（chat_message の None/文字列 で後段の分岐に入る）


############################################################
# 7. チャット送信時の処理（描画先は messages_container）
#   目的：
#    - 送信直後の“その回”のユーザー発言とAI回答を messages_container に追加描画
#    - 会話内容を session_state.messages に追記（再実行時の再生用）
############################################################
if chat_message:
    # ユーザー送信内容とモードをログへ
    logger.info({"message": chat_message, "application_mode": st.session_state.mode})

    # --- 描画は messages_container（= 入力欄の上）に追加する ---
    with messages_container:
        # ユーザー発言（右カラムのチャットUI）
        with st.chat_message("user"):
            st.markdown(chat_message)

        # LLM呼び出し（RAG実行中はスピナー表示）
        with st.spinner(ct.SPINNER_TEXT):
            try:
                llm_response = utils.get_llm_response(chat_message)
            except Exception as e:
                logger.error(f"{ct.GET_LLM_RESPONSE_ERROR_MESSAGE}\n{e}")
                st.error(utils.build_error_message(ct.GET_LLM_RESPONSE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
                st.stop()

        # アシスタント回答（モードにより表示形式を切替）
        try:
            with st.chat_message("assistant"):
                if st.session_state.mode == ct.ANSWER_MODE_1:
                    # 「社内文書検索」：参照ファイル（ページNo付き）を提示
                    content = cn.display_search_llm_response(llm_response)
                else:
                    # 「社内問い合わせ」：回答＋参照元を提示
                    content = cn.display_contact_llm_response(llm_response)

            # AIの出力もログへ（トレース用）
            logger.info({"message": content, "application_mode": st.session_state.mode})

        except Exception as e:
            logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
            st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            st.stop()

    # --- 会話履歴を保存（再実行時に display_conversation_log で再生するため） ---
    st.session_state.messages.append({"role": "user", "content": chat_message})
    st.session_state.messages.append({"role": "assistant", "content": content})
