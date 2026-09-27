import os
import re
from dotenv import load_dotenv
from google import genai
from fetch_data import fetch_data

# 環境変数の読み込み
load_dotenv()

# ==========================================
# 統計フィルター判定ロジック（バックテスト検証済み）
# ==========================================

def is_sum_in_range(numbers, min_sum=90, max_sum=170):
    """【和の範囲】 7つの数字の合計が90〜170の範囲内か"""
    return min_sum <= sum(numbers) <= max_sum

def is_odd_even_balanced(numbers, allowed_ratios=[(3, 4), (4, 3), (2, 5), (5, 2)]):
    """【奇偶比率】 3:4, 4:3, 2:5, 5:2"""
    odd_count = sum(1 for x in numbers if x % 2 != 0)
    return (odd_count, 7 - odd_count) in allowed_ratios

def is_consecutive_valid(numbers, max_consecutive=2):
    """【連続数制限】 3連番以上を除外"""
    sorted_nums = sorted(numbers)
    consecutive_count = 0
    max_count = 0
    for i in range(len(sorted_nums) - 1):
        if sorted_nums[i+1] == sorted_nums[i] + 1:
            consecutive_count += 1
            max_count = max(max_count, consecutive_count)
        else:
            consecutive_count = 0
    return max_count < max_consecutive

def is_high_low_balanced(numbers, threshold=19, allowed_ratios=[(3, 4), (4, 3), (2, 5), (5, 2)]):
    """【高低バランス】 18以下(Low) と 19以上(High) の配分"""
    low_count = sum(1 for x in numbers if x < threshold)
    return (low_count, 7 - low_count) in allowed_ratios

def validate_combination(numbers):
    """4つの統計フィルターをすべてクリアしているか検証"""
    if len(numbers) != 7 or len(set(numbers)) != 7:
        return False
    return (
        is_sum_in_range(numbers) and
        is_odd_even_balanced(numbers) and
        is_consecutive_valid(numbers) and
        is_high_low_balanced(numbers)
    )

# ==========================================
# Gemini 予測生成メイン処理
# ==========================================

def generate_predictions(df=None, api_key=None, *args, **kwargs):
    """
    Gemini APIを使用してロト7の予測を生成するメイン関数。
    Streamlit (app.py) および CLI (run.py) の両方の呼び出しに対応。
    """
    # APIキーの取得（引数 > Streamlit Secrets > .env の順で検索）
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass

    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません。.env または Streamlit Secrets を確認してください。")

    # 過去データの安全な補完（dfがNoneまたは空データフレームの場合は自動取得）
    if df is None or (hasattr(df, 'empty') and df.empty):
        df = fetch_data()

    if df is None or (hasattr(df, 'empty') and df.empty):
        return "⚠️ 過去データの取得に失敗しました。画面左の「最新当選データの取得」ボタンを押してから再度お試しください。"

    client = genai.Client(api_key=api_key)

    recent_df = df.tail(10)
    latest_draw_num = len(df)
    next_draw_num = latest_draw_num + 1

    prompt = f"""
あなたはロト7のデータ分析プロフェッショナルです。
直近10回の当選データ（第{latest_draw_num-9}回〜第{latest_draw_num}回）を参考にして、次回（第{next_draw_num}回）の最適買い目を提案してください。

【厳格な統計フィルター条件】
生成するすべての買い目（7つの数字）は、以下の統計ルールを**絶対に厳守**してください：
1. **合計値**: 7つの数字の合計は 90 〜 170 の範囲内。
2. **奇偶バランス**: 奇数と偶数の比率は 3:4, 4:3, 2:5, 5:2 のいずれか。
3. **連続数**: 3連番以上（例: 10,11,12）は含めない（2連番までは許可）。
4. **高低バランス**: 1〜18（Low）と 19〜37（High）の比率は 3:4, 4:3, 2:5, 5:2 のいずれか。

【出力フォーマット】
以下の形式で必ず5パターンの買い目を挙げ、その後に簡単な分析・戦略方針を添えてください。
各買い目は必ず `[数字1, 数字2, 数字3, 数字4, 数字5, 数字6, 数字7]` の形式で記述してください。

買い目1: [x, x, x, x, x, x, x]
買い目2: [x, x, x, x, x, x, x]
買い目3: [x, x, x, x, x, x, x]
買い目4: [x, x, x, x, x, x, x]
買い目5: [x, x, x, x, x, x, x]

直近の傾向分析と戦略方針:
（分析テキスト）
"""

    # API呼び出し（利用制限・エラー時のハンドリング付き）
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )
        output_text = response.text
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return "⚠️ APIの利用制限（1分あたりのリクエスト上限）に達しました。\n1分ほど時間をおいてから、再度「予測を実行する」ボタンを押してください。"
        return f"⚠️ API実行中にエラーが発生しました: {error_msg}"

    # Python側でのダブルチェック（検証＆フィルタリングログの付加）
    lines = output_text.split('\n')
    validated_lines = []
    
    for line in lines:
        if "買い目" in line and "[" in line and "]" in line:
            match = re.search(r'\[(.*?)\]', line)
            if match:
                try:
                    nums = [int(n.strip()) for n in match.group(1).split(',')]
                    nums = sorted(nums)
                    is_valid = validate_combination(nums)
                    status_tag = " (✅ 統計フィルター合格)" if is_valid else " (⚠️ 統計境界外)"
                    line = f"{line}{status_tag}"
                except ValueError:
                    pass
        validated_lines.append(line)

    return "\n".join(validated_lines)