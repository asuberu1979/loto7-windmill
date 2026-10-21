import streamlit as st
import datetime
from gemini_engine import generate_predictions

# ページ基本設定
st.set_page_config(
    page_title="PROJECT WINDMILL - Loto7 Pure Python Engine",
    page_icon="🎯",
    layout="wide"
)

# ヘッダー情報
st.title("🎯 PROJECT WINDMILL")
st.subheader("アスベル式・未来逆算理論 × 統計解析エンジン（Pure Python）")
st.caption("Zero-API / High-Speed Statistical Processing")

st.markdown("---")

# 2カラムレイアウト
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📊 予測の実行")
    st.markdown("「予測を実行」ボタンを押すと、過去データを瞬時に統計解析し、最適な5つの組み合わせを提案します。")
    
    # 実行ボタン
    if st.button("🚀 予測を実行する", type="primary", use_container_width=True):
        with st.spinner("統計解析室：確率波の収束計算および条件フィルター検証中..."):
            # ピュアPythonエンジンを呼び出し
            report_text = generate_predictions()
            st.session_state["report_text"] = report_text

with col2:
    st.markdown("### 📋 予測結果")
    
    # 結果がセッションに保持されている場合のみ表示
    if "report_text" in st.session_state:
        st.success("予測の生成が完了しました！")
        
        # レポート本文を表示
        st.markdown(st.session_state["report_text"])
        
        st.markdown("---")
        
        # ダウンロード機能
        today_str = datetime.date.today().strftime("%Y%m%d")
        st.download_button(
            label="📥 予想結果をテキストファイル (.txt) でダウンロード",
            data=st.session_state["report_text"],
            file_name=f"loto7_prediction_{today_str}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.info("左側の「予測を実行する」ボタンを押してください。")