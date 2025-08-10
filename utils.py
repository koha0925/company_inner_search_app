"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
- アイコン種別の判定、エラーメッセージ整形
- RAG（履歴考慮リトリーバ）× 会話チェーンの組み立てと実行
"""

############################################################
# ライブラリの読み込み
############################################################
import os
from dotenv import load_dotenv
import streamlit as st
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage  # ※ 会話履歴への追加で使用
from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import constants as ct


############################################################
# 設定関連
############################################################
# 「.env」ファイルで定義した環境変数を読み込む
# - OpenAI API キーなどを環境変数から利用できるようにする
load_dotenv()


############################################################
# 関数定義
############################################################

def get_source_icon(source: str) -> str:
    """
    参照元（source）の種類に応じたアイコン（Material Symbols）を返す

    Args:
        source: 参照元のありか（URL or ファイルパス）

    Returns:
        str: Streamlit用のアイコン表現（例: :material/link:）
    """
    # 参照元がWebページ（http/https）ならリンクのアイコン、それ以外（ファイル）はドキュメントのアイコン
    if source.startswith("http"):
        return ct.LINK_SOURCE_ICON
    return ct.DOC_SOURCE_ICON


def build_error_message(message: str) -> str:
    """
    エラーメッセージと、共通の問い合わせテンプレートを結合して返す

    Args:
        message: 表示したいエラーメッセージ本文

    Returns:
        str: 画面表示用の連結メッセージ
    """
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])


def get_llm_response(chat_message: str):
    """
    LLM から回答を取得して返す（RAG + 会話履歴考慮）

    フロー概要：
      1) ChatOpenAI を準備（モデル・温度は constants.py で一元管理）
      2) 履歴を踏まえた「質問の言い換え」用プロンプトを作成
      3) モードに応じた本問合せプロンプト（文書検索 or 社内問い合わせ）を用意
      4) 履歴考慮リトリーバ + スタッフィングチェーンで RAG チェーンを構築
      5) チェーンに input（= ユーザー入力）と chat_history を渡して実行
      6) レスポンスを chat_history に追加（次ターンでの文脈維持用）

    Args:
        chat_message: ユーザーの入力文字列

    Returns:
        LangChain のチェーンが返す辞書（answer, context などを含む）
    """
    # 1) LLM本体の用意（モデル名・温度は constants 側で集中管理）
    llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE)

    # 2) 履歴を踏まえた「独立した質問」生成プロンプト
    #    - 会話履歴が長くなっても、検索に最適化されたクエリを毎回生成できる
    question_generator_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ct.SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    # 3) モード別の本問合せプロンプト（文書検索 / 社内問い合わせ）
    if st.session_state.mode == ct.ANSWER_MODE_1:
        # 社内文書検索：関連がなければ「該当資料なし」を厳格に返す設計
        question_answer_template = ct.SYSTEM_PROMPT_DOC_SEARCH
    else:
        # 社内問い合わせ：文脈に基づき Markdown 詳細回答。必要に応じ一般情報も許容
        question_answer_template = ct.SYSTEM_PROMPT_INQUIRY

    question_answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_answer_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    # 4) 履歴考慮リトリーバ + RAG チェーンを構築
    #    - 「独立した質問」生成 → retriever で検索 → 文脈を stuff して回答生成、の流れ
    history_aware_retriever = create_history_aware_retriever(
        llm, st.session_state.retriever, question_generator_prompt
    )
    question_answer_chain = create_stuff_documents_chain(llm, question_answer_prompt)
    chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # 5) チェーンを実行（input と chat_history を渡す）
    llm_response = chain.invoke({
        "input": chat_message,
        "chat_history": st.session_state.chat_history
    })

    # 6) 会話履歴へ今回のターンを追加
    #    - HumanMessage はオブジェクト、LLM 側は llm_response["answer"]（str）をそのまま保存。
    #      ※ より厳密に型を揃えるなら AIMessage(content=...) を使う方法もある。
    st.session_state.chat_history.extend([
        HumanMessage(content=chat_message),
        llm_response["answer"]
    ])

    return llm_response
