"""
このファイルは、画面表示に特化した関数定義のファイルです。
- タイトルやモード選択などのUI断片（コンポーネント）を関数として提供します。
- main.py から呼び出され、レイアウトに従って描画されます。
"""

############################################################
# ライブラリの読み込み
############################################################
import streamlit as st
import utils
import constants as ct


############################################################
# 関数定義
############################################################

def display_app_title():
    """
    タイトル表示
    - ブラウザタブ名（set_page_config）とは別に、画面上部の見出しを出します。
    - スタイルは Streamlit の見出し（##）に委譲します。
    """
    st.markdown(f"## {ct.APP_NAME}")


def display_select_mode(container=None, show_header=False):
    """
    回答モードのラジオボタンを表示
    - container が与えられたら、その文脈の中で描画（左カラムなど）。
    - show_header=True の場合は、この関数内でも見出しを出す（通常は外側で見出しを出すので False）。
    - 選択結果は st.session_state.mode に保存（既定=ANSWER_MODE_1）。
    """
    tgt = container if container is not None else st

    # 既定のモード（未設定時のみ）
    if "mode" not in st.session_state:
        st.session_state.mode = ct.ANSWER_MODE_1

    def body():
        # 外側で見出しを描く構成のため、デフォルトは隠す
        if show_header:
            st.subheader("利用目的")

        # ラジオボタン本体（label は設定するが画面には非表示）
        st.session_state.mode = st.radio(
            label="利用目的",
            options=[ct.ANSWER_MODE_1, ct.ANSWER_MODE_2],
            label_visibility="collapsed",
        )

    # container が指定されていればその中に、なければ通常コンテキストに描画
    if container is not None:
        with container:
            body()
    else:
        body()


def display_examples_block():
    """
    左カラムに置く「利用目的ごとの説明＋入力例」エリア
    - タイトル（太字）→ 説明（info）→ 入力例（白ボックス）という順で統一。
    - 見た目は main.py の CSS（.sec-title / .example-box）で調整。
    """
    # --- 社内文書検索 ---
    st.markdown('<div class="sec-title">【「社内文書検索」を選択した場合】</div>', unsafe_allow_html=True)
    st.info("入力内容と関連性が高い社内文書のありかを検索できます。")
    st.markdown("""
        <div class="example-box">
        <b>【入力例】</b><br>
        社員の育成方針に関するMTGの議事録
        </div>
    """, unsafe_allow_html=True)

    # --- 社内問い合わせ ---
    st.markdown('<div class="sec-title">【「社内問い合わせ」を選択した場合】</div>', unsafe_allow_html=True)
    st.info("質問・要望に対して、社内文書の情報をもとに回答を得られます。")
    st.markdown("""
        <div class="example-box">
        <b>【入力例】</b><br>
        人事部に所属している従業員情報を一覧化して
        </div>
    """, unsafe_allow_html=True)


def display_initial_ai_message():
    """
    右カラム上部の初期メッセージ（assistant 気泡内）
    - 緑ボックス（ai-message-box）は CSS で色・余白・角丸を付与（main.py 側の <style>）。
    - 注意書きは Streamlit の st.warning を使用し、Material Symbols アイコンを付与。
    """
    with st.chat_message("assistant"):
        # 緑の案内ボックス
        st.markdown("""
            <div class="ai-message-box">
            こんにちは。私は社内文書の情報をもとに回答する生成AIチャットボットです。<br>
            左の「利用目的」を選択し、右下の入力欄からメッセージを送信してください。
            </div>
        """, unsafe_allow_html=True)

        # 黄色の注意ボックス（Streamlit 標準UIを利用、CSSは main.py で上書き）
        st.warning(
            "具体的に入力すると、より期待通りの回答が得やすくなります。",
            icon=":material/warning:"
        )


def display_conversation_log():
    """
    会話ログの一覧表示
    """
    def _page_label(meta_page):
        """0始まりの可能性に配慮して、人間向けのページNo文字列を返す"""
        try:
            p = int(meta_page)
            if p >= 0:
                return f"（ページNo.{p + 1}）"
        except Exception:
            pass
        return f"（ページNo.{meta_page}）"

    # 会話ログのループ処理
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):

            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                # 「社内文書検索」の場合
                if message["content"]["mode"] == ct.ANSWER_MODE_1:

                    if "no_file_path_flg" not in message["content"]:
                        # ===== メイン文書 =====
                        st.markdown(message["content"]["main_message"])
                        icon = utils.get_source_icon(message['content']['main_file_path'])
                        if "main_page_number" in message["content"]:
                            st.success(
                                f"{message['content']['main_file_path']}　{_page_label(message['content']['main_page_number'])}",
                                icon=icon
                            )
                        else:
                            st.success(f"{message['content']['main_file_path']}", icon=icon)

                        # ===== サブ文書 =====
                        if "sub_message" in message["content"]:
                            st.markdown(message["content"]["sub_message"])
                            for sub_choice in message["content"]["sub_choices"]:
                                icon = utils.get_source_icon(sub_choice['source'])
                                if "page_number" in sub_choice:
                                    st.info(
                                        f"{sub_choice['source']}　{_page_label(sub_choice['page_number'])}",
                                        icon=icon
                                    )
                                else:
                                    st.info(f"{sub_choice['source']}", icon=icon)

                    else:
                        st.markdown(message["content"]["answer"])

                # 「社内問い合わせ」の場合
                else:
                    st.markdown(message["content"]["answer"])
                    if "file_info_list" in message["content"]:
                        st.divider()
                        st.markdown(f"##### {message['content']['message']}")
                        for file_info in message["content"]["file_info_list"]:
                            icon = utils.get_source_icon(file_info)
                            st.info(file_info, icon=icon)



def display_search_llm_response(llm_response):
    """
    モード1（社内文書検索）の LLMレスポンス表示
    - context[0] をメイン文書、以降をサブ候補として扱い、
      ページ番号があれば「（ページNo.X）」を付与して表示します。
    - 0始まりの page に配慮して、人向け表記は +1 して出力。
    - 返り値（content）は会話ログの再生用データ。
    """
    def _page_label(meta_page):
        """0始まりの可能性に配慮して、人間向けのページNo文字列を返す"""
        try:
            p = int(meta_page)
            if p >= 0:
                return f"（ページNo.{p + 1}）"
        except Exception:
            pass
        return f"（ページNo.{meta_page}）"

    # 参照元があり、かつ「該当資料なし」でないとき
    if llm_response["context"] and llm_response["answer"] != ct.NO_DOC_MATCH_ANSWER:

        # ===== メイン文書 =====
        main_meta = llm_response["context"][0].metadata
        main_file_path = main_meta.get("source", "")
        main_message = "入力内容に関する情報は、以下のファイルに含まれている可能性があります。"
        st.markdown(main_message)

        icon = utils.get_source_icon(main_file_path)
        # ページ番号があれば末尾に付与
        if "page" in main_meta:
            main_page_number = main_meta["page"]
            display_text = f"{main_file_path}　{_page_label(main_page_number)}"
        else:
            main_page_number = None
            display_text = main_file_path

        st.success(display_text, icon=icon)

        # ===== サブ文書 =====
        sub_choices = []
        duplicate_check_list = []

        for document in llm_response["context"][1:]:
            sub_meta = document.metadata
            sub_file_path = sub_meta.get("source", "")

            # 同一ファイルの重複表示を避ける
            if sub_file_path == main_file_path:
                continue
            if sub_file_path in duplicate_check_list:
                continue
            duplicate_check_list.append(sub_file_path)

            # ページ番号付きの候補を作成
            if "page" in sub_meta:
                sub_choices.append({"source": sub_file_path, "page_number": sub_meta["page"]})
            else:
                sub_choices.append({"source": sub_file_path})

        if sub_choices:
            sub_message = "その他、ファイルありかの候補を提示します。"
            st.markdown(sub_message)

            for sub_choice in sub_choices:
                icon = utils.get_source_icon(sub_choice["source"])
                if "page_number" in sub_choice:
                    display_text = f"{sub_choice['source']}　{_page_label(sub_choice['page_number'])}"
                else:
                    display_text = sub_choice["source"]
                st.info(display_text, icon=icon)

        # ===== 会話ログ用の戻り値（再実行時の再生に使う） =====
        content = {
            "mode": ct.ANSWER_MODE_1,
            "main_message": main_message,
            "main_file_path": main_file_path,
        }
        if "page" in main_meta:
            content["main_page_number"] = main_meta["page"]
        if sub_choices:
            content["sub_message"] = sub_message
            content["sub_choices"] = sub_choices

    else:
        # 該当なし（固定メッセージをそのまま表示）
        st.markdown(ct.NO_DOC_MATCH_MESSAGE)
        content = {
            "mode": ct.ANSWER_MODE_1,
            "answer": ct.NO_DOC_MATCH_MESSAGE,
            "no_file_path_flg": True,
        }

    return content


def display_contact_llm_response(llm_response):
    """
    「社内問い合わせ」モードにおけるLLMレスポンスを表示

    - 回答本文を表示
    - 参照元がある場合は、ファイルパスにページ番号があれば（ページNo.X）を付けて表示
    - 返り値（content）は会話ログの再生用データ
    """
    # 0始まりの可能性に配慮して、人間向けのページNo文字列を返す
    def _page_label(meta_page):
        try:
            p = int(meta_page)
            if p >= 0:
                return f"（ページNo.{p + 1}）"
        except Exception:
            pass
        return f"（ページNo.{meta_page}）"

    # 回答本文
    st.markdown(llm_response["answer"])

    file_info_list = []  # 表示した参照元（文字列）を格納（会話ログ用に保存）

    # 「社内文書に情報がなかった」以外の場合は情報源を表示
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        st.divider()
        message = "情報源"
        st.markdown(f"##### {message}")

        seen_paths = set()  # 同一ファイル重複抑止

        for document in llm_response["context"]:
            file_path = document.metadata.get("source", "")
            if not file_path or file_path in seen_paths:
                continue
            seen_paths.add(file_path)

            # ページ番号があれば末尾に付与
            if "page" in document.metadata:
                display_text = f"{file_path}　{_page_label(document.metadata['page'])}"
            else:
                display_text = file_path

            icon = utils.get_source_icon(file_path)
            st.info(display_text, icon=icon)

            file_info_list.append(display_text)

    # 会話ログ再生用のデータを返す
    content = {
        "mode": ct.ANSWER_MODE_2,
        "answer": llm_response["answer"],
    }
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        content["message"] = message
        content["file_info_list"] = file_info_list

    return content

