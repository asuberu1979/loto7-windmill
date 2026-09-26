import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# 既存モジュールのインポート
from fetch_data import fetch_data
from analyzer import Loto7Analyzer
from gemini_engine import generate_predictions

# 1. 環境変数の取得（ローカルの.env と Streamlit CloudのSecrets両対応）
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

# 2. ページ基本設定
st.set_page_config(
    page_title="PROJECT WINDMILL | Loto7 AI Analysis",
    page_icon="🎰",
    layout="wide"
)

# カスタムCSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 3em;
        font-size: 18px !important;
        font-weight: bold !important;
        background-color: #2E7D32 !important;
        color: white !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. ヘッダー部分
st.title("🎯 PROJECT WINDMILL - Loto7 AI 予測システム")
st.caption("統計データ解析 × AI（Gemini）による戦略的買目算出")

st.divider()

# 4. サイドバー設定
st.sidebar.header("⚙️ 設定・データ更新")

if st.sidebar.button("最新当選データの取得"):
    with st.spinner("最新データを取得中..."):
        try:
            fetch_data()
            st.sidebar.success("最新データの更新が完了しました！")
        except Exception as e:
            st.sidebar.error(f"データ取得エラー: {e}")

# 5. メイン画面：実行ボタンと処理
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 予測の実行")
    st.write("「予測を実行」ボタンを押すと、過去データを自動解析し、Gemini AIが最適な5つの組み合わせを提案します。")
    
    run_btn = st.button("🚀 予測を実行する", key="run_prediction")

    # ★503エラーに関する注意書き
    st.caption("ℹ️ **エラー（503 UNAVAILABLE等）が表示された場合**\nGoogle AIサーバーの混雑による一時的なエラーです。数秒置いてからもう一度ボタンを押してください。")

with col2:
    st.subheader("📋 予測結果")
    
    if run_btn:
        if not api_key:
            st.error("APIキーが見つかりません。`.env` または Streamlit Secrets を確認してください。")
        else:
            with st.spinner("統計分析を実施し、Gemini AIが最適な5パターンを考案中..."):
                try:
                    analyzer = Loto7Analyzer()
                    analysis_summary = analyzer.run_analysis()
                    predictions = generate_predictions(analysis_summary, api_key)

                    st.success("予測の生成が完了しました！")
                    st.text_area("生成結果", predictions, height=450)
                    
                except Exception as e:
                    st.error(f"処理中にエラーが発生しました: {e}")
                    if "503" in str(e):
                        st.warning("💡 **503エラーへの対処法**: Google AIサーバーが一過性の混雑状態です。10秒ほど待ってから再度「🚀 予測を実行する」を押すと成功します。")
    else:
        st.info("左側の「🚀 予測を実行する」ボタンを押してください。")

# 6. 下部データ確認タブ
st.divider()
st.subheader("📈 データ分析データ")

tab1, tab2 = st.tabs(["📄 直近のデータ", "ℹ️ システム概要"])

with tab1:
    if os.path.exists("loto7_data.csv"):
        df = pd.read_csv("loto7_data.csv")
        st.dataframe(df.tail(10), use_container_width=True)
    else:
        st.write("データファイルが存在しません。サイドバーから最新データを取得してください。")

with tab2:
    st.markdown("""
    - **データソース**: mk-mode.com (`LOTO7_ALL.csv`)
    - **分析エンジン**: 軸数字頻度・相性マトリクス解析
    - **AIモデル**: `gemini-3.8-flash`
    """)