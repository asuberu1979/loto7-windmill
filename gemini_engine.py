import os
import re
import json
import requests
from dotenv import load_dotenv
from fetch_data import fetch_data

# 環境変数の読み込み
load_dotenv()

# ==========================================
# 統計フィルター判定ロジック
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
# OpenRouter 経由の予測生成メイン処理
# ==========================================

def generate_predictions(df=None, api_key=None, *args, **kwargs):
    """
    OpenRouter APIを使用してロト7の予測を生成するメイン関数。
    """
    # OpenRouter APIキーの取得
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("OPENROUTER_API_KEY")
        except Exception:
            pass

    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return "⚠️ OPENROUTER_API_KEY が設定されていません。Streamlit Secrets または .env を確認してください。"

    # 過去データ自動取得
    if df is None or (hasattr(df, 'empty') and df.empty):
        df = fetch_data()

    if df is None or (hasattr(df, 'empty') and df.empty):
        return "⚠️ 過去データの取得に失敗しました。画面左の「最新当選データの取得」を押してください。"

    latest_draw_num = len(df)
    next_draw_num = latest_draw_num + 1

    # 直近10回のデータを文字列として抽出（AIに読ませるため）
    recent_df = df.tail(10)
    recent_data_str = recent_df.to_string(index=False)

    prompt = f"""
あなたはロト7の高度なデータ分析プロフェッショナルです。
以下の「直近10回の当選データ」を分析し、次回（第{next_draw_num}回）の最適買い目を5パターン提案してください。

【直近10回の当選データ】
{recent_data_str}

【最重要：軸数字と重複の強制ルール】
1. **軸数字（ホットナンバー）を2〜3個指定すること**:
   直近10回で出現率が高い数字や強力な傾向を持つ数字を「軸数字」として2〜3個選出してください。
2. **軸数字の強制重複**:
   選んだ軸数字は、5つの買い目のうち**少なくとも3パターン以上に重複して組み込んでください**。
3. **数字の完全分散（全37数字のパズル配置）は絶対禁止**:
   5パターンで全数字を網羅しようとしないでください。根拠の薄い数字は除外し、強い数字に買い目を集中させてリアリティのある予想にしてください。

【厳格な統計フィルター条件】
生成するすべての買い目（7つの数字）は、以下の統計ルールを**絶対に厳守**してください：
1. **合計値**: 7つの数字の合計は 90 〜 170 の範囲内。
2. **奇偶バランス**: 奇数と偶数の比率は 3:4, 4:3, 2:5, 5:2 のいずれか。
3. **連続数**: 3連番以上（例: 10,11,12）は含めない（2連番までは許可）。
4. **高低バランス**: 1〜18（Low）と 19〜37（High）の比率は 3:4, 4:3, 2:5, 5:2 のいずれか。

【出力フォーマット】
以下の形式で必ず5パターンの買い目を挙げ、その後に選定理由・分析方針を添えてください。
各買い目は必ず `[数字1, 数字2, 数字3, 数字4, 数字5, 数字6, 数字7]` の形式で記述してください。

買い目1: [x, x, x, x, x, x, x]
買い目2: [x, x, x, x, x, x, x]
買い目3: [x, x, x, x, x, x, x]
買い目4: [x, x, x, x, x, x, x]
買い目5: [x, x, x, x, x, x, x]

直近の傾向分析と選定理由:
・選出した軸数字とその選定根拠（直近での出現回数など具体的に）
・各買い目の戦略とポートフォリオの意図
"""

    # OpenRouter API エンドポイントの設定
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Loto7 AI Analysis"
    }

    payload = {
        "model": "google/gemini-3.7-flash",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        res_data = response.json()

        if response.status_code != 200:
            error_msg = res_data.get("error", {}).get("message", response.text)
            return f"⚠️ OpenRouter API エラー ({response.status_code}): {error_msg}"

        output_text = res_data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"⚠️ 通信エラーが発生しました: {str(e)}"

    # Python側でのダブルチェック
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