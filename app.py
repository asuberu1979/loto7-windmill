import streamlit as st
import pandas as pd
from fetch_data import fetch_data
from gemini_engine import generate_predictions

st.set_page_config(page_title="PROJECT WINDMILL | Loto7 AI Analysis", layout="wide")

st.title("🎯 PROJECT WINDMILL - LOTO7 AI 予測システム")
st.caption("統計データ解析 × AI（Gemini）による戦略的買い目算出")

# データの初期ロード
if "df" not in st.session_state:
    st.session_state.df = fetch_data()

# サイドバー
st.sidebar.header("⚙️ 設定・データ更新")
if st.sidebar.button("最新当選データの取得"):
    with st.spinner("最新データを取得中..."):
        st.session_state.df = fetch_data()
        st.sidebar.success("データ更新完了！")

# メイン表示
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 予測の実行")
    st.write("「予測を実行」ボタンを押すと、過去データを自動解析し、Gemini AIが最適な5つの組み合わせを提案します。")
    
    if st.button("🚀 予測を実行する"):
        with st.spinner("Gemini AIが最適買い目を計算中..."):
            result = generate_predictions(df=st.session_state.df)
            st.session_state.last_result = result

with col2:
    st.subheader("📋 予測結果")
    if "last_result" in st.session_state:
        st.success("予測の生成が完了しました！")
        st.write(st.session_state.last_result)
    else:
        st.info("左側の「予測を実行する」ボタンを押してください。")

# データ分析領域
st.divider()
st.subheader("📈 データ分析データ")
tab1, tab2 = st.tabs(["📜 直近のデータ", "ℹ️ 概要"])

with tab1:
    if st.session_state.df is not None:
        st.dataframe(st.session_state.df.tail(10), use_container_width=True)

with tab2:
    st.write("""
    **当システムの統計フィルター基準**
    - **和の範囲**: 90 〜 170
    - **奇偶比率**: 3:4, 4:3, 2:5, 5:2
    - **連続数制限**: 3連番以上除外
    - **高低バランス**: 18以下（Low）/ 19以上（High）
    """)