import streamlit as st
import datetime
from combo_engine import generate_predictions

# ページ基本設定
st.set_page_config(
    page_title="PROJECT WINDMILL - Loto7 Combination Generator",
    page_icon="🎯",
    layout="wide"
)

# ヘッダー情報
st.title("🎯 PROJECT WINDMILL")
st.subheader("アスベル式・未来逆算理論 × 条件フィルター生成エンジン（Pure Python）")
st.caption("Zero-API / Entertainment Use")

st.markdown("---")

# 2カラムレイアウト
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📊 組み合わせの生成")
    st.markdown(
        "「生成する」ボタンを押すと、直近の出現傾向から軸数字を選び、"
        "条件フィルターを通した5つの組み合わせをランダムに生成します。"
    )
    st.caption("ロト7は毎回独立した抽せんで、どの組み合わせも当せん確率は同じです。エンタメとしてお楽しみください。")

    # 実行ボタン
    if st.button("🚀 組み合わせを生成する", type="primary", use_container_width=True):
        with st.spinner("データを取得して、軸数字の選定と条件フィルターの検証中..."):
            report_text = generate_predictions()
            st.session_state["report_text"] = report_text

with col2:
    st.markdown("### 📋 生成結果")

    # 結果がセッションに保持されている場合のみ表示
    if "report_text" in st.session_state:
        st.success("生成が完了しました！")

        # レポート本文を表示
        st.markdown(st.session_state["report_text"])

        st.markdown("---")

        # ダウンロード機能
        today_str = datetime.date.today().strftime("%Y%m%d")
        st.download_button(
            label="📥 生成結果をテキストファイル (.txt) でダウンロード",
            data=st.session_state["report_text"],
            file_name=f"loto7_combinations_{today_str}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.info("左側の「組み合わせを生成する」ボタンを押してください。")
