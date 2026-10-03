import os
import re
import json
import requests
from dotenv import load_dotenv
from fetch_data import fetch_data

# 環境変数の読み込み
load_dotenv()

# ==========================================
# 統計解析室 (Python) : フィルター判定ロジック
# ==========================================
def is_sum_in_range(numbers, min_sum=90, max_sum=170):
    return min_sum <= sum(numbers) <= max_sum

def is_odd_even_balanced(numbers, allowed_ratios=[(3, 4), (4, 3), (2, 5), (5, 2)]):
    odd_count = sum(1 for x in numbers if x % 2 != 0)
    return (odd_count, 7 - odd_count) in allowed_ratios

def is_consecutive_valid(numbers, max_consecutive=2):
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
    low_count = sum(1 for x in numbers if x < threshold)
    return (low_count, 7 - low_count) in allowed_ratios

def validate_combination(numbers):
    if len(numbers) != 7 or len(set(numbers)) != 7:
        return False
    return (
        is_sum_in_range(numbers) and
        is_odd_even_balanced(numbers) and
        is_consecutive_valid(numbers) and
        is_high_low_balanced(numbers)
    )

# ==========================================
# OpenRouter API 汎用呼び出し関数
# ==========================================
def call_openrouter(model_id, system_prompt, user_prompt, api_key):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Loto7 AI Prediction Institute"
    }
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=45)
    res_data = response.json()
    
    if response.status_code != 200:
        raise Exception(res_data.get("error", {}).get("message", response.text))
        
    return res_data["choices"][0]["message"]["content"]

# ==========================================
# 研究所長統括：マルチエージェント・パイプライン
# ==========================================
def generate_predictions(df=None, api_key=None, *args, **kwargs):
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("OPENROUTER_API_KEY")
        except Exception:
            pass
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "⚠️ OPENROUTER_API_KEY が設定されていません。"

    if df is None or (hasattr(df, 'empty') and df.empty):
        df = fetch_data()
    if df is None or (hasattr(df, 'empty') and df.empty):
        return "⚠️ 過去データの取得に失敗しました。"

    next_draw_num = len(df) + 1
    recent_df = df.tail(10)
    recent_data_str = recent_df.to_string(index=False)

    try:
        # --------------------------------------------------
        # 第1フェーズ: 調査官 (Gemini Flash)
        # --------------------------------------------------
        gemini_system = "あなたは直近のデータから出現トレンドとホットナンバーを抽出する『調査官』です。"
        gemini_prompt = f"""
以下の直近10回のロト7当選データから、次回（第{next_draw_num}回）の「最重要軸数字」を3つ選定し、その理由（出現回数や勢い）を簡潔に報告してください。
【直近10回の当選データ】\n{recent_data_str}
"""
        investigation_report = call_openrouter("google/gemini-2.5-flash", gemini_system, gemini_prompt, api_key)

        # --------------------------------------------------
        # 第2フェーズ: 仮説研究員 (GPT-5.6 Terra 相当 -> GPT-4o)
        # --------------------------------------------------
        gpt_system = "あなたは指定された軸数字を使って、バリエーション豊かな買い目を構築する『仮説研究員』です。"
        gpt_prompt = f"""
調査官から以下の分析報告が届きました：
【調査報告】
{investigation_report}

この報告にある「3つの軸数字」を使い、次回（第{next_draw_num}回）のロト7の買い目を5パターン構築してください。
条件：
1. 調査官が選定した軸数字は、5パターンのうち「3パターン以上」に必ず重複して組み込むこと。
2. 数字を均等に散らしたパズル配置は禁止。強い数字を中心にポートフォリオを組むこと。
3. ロト7は1〜37の数字から7つを選びます。
"""
        hypothesis_report = call_openrouter("openai/gpt-5.6-terra", gpt_system, gpt_prompt, api_key)

        # --------------------------------------------------
        # 第3フェーズ: 査読委員 (Claude Sonnet 5.5 相当 -> Claude 3.5 Sonnet)
        # --------------------------------------------------
        claude_system = "あなたは提出された予想買い目を厳格に監査し、最終出力を生成する『査読委員』です。"
        claude_prompt = f"""
仮説研究員が以下の買い目案を提出しました：
【買い目案】
{hypothesis_report}

以下の【厳格な査読基準】に照らし合わせ、問題があれば修正して、最終的な5パターンの買い目を確定させてください。

【査読基準】
1. 軸数字が複数の買い目にしっかり「重複」して組み込まれているか（均等分散パズルになっていないか）。
2. 全ての買い目が以下のルールを満たしているか：
   - 7つの数字の合計が90〜170の範囲内。
   - 奇偶比が「3:4, 4:3, 2:5, 5:2」のいずれか。
   - 3連番以上（例:10,11,12）が含まれていない（2連番までは許可）。
   - 高低バランス（1〜18と19〜37）が「3:4, 4:3, 2:5, 5:2」のいずれか。

【最終出力フォーマット】
以下の形式で5パターンの買い目と、確定した戦略方針を出力してください。
買い目1: [x, x, x, x, x, x, x]
買い目2: [x, x, x, x, x, x, x]
買い目3: [x, x, x, x, x, x, x]
買い目4: [x, x, x, x, x, x, x]
買い目5: [x, x, x, x, x, x, x]

最終戦略と軸数字の選定理由:
（テキスト）
"""
        final_output = call_openrouter("anthropic/claude-sonnet-5.5", claude_system, claude_prompt, api_key)

    except Exception as e:
        return f"⚠️️ 研究所ネットワーク（API）通信エラーが発生しました: {str(e)}"

    # --------------------------------------------------
    # 最終フェーズ: 統計解析室 (Pythonバリデーション)
    # --------------------------------------------------
    lines = final_output.split('\n')
    validated_lines = []
    
    for line in lines:
        if "買い目" in line and "[" in line and "]" in line:
            match = re.search(r'\[(.*?)\]', line)
            if match:
                try:
                    nums = [int(n.strip()) for n in match.group(1).split(',')]
                    nums = sorted(nums)
                    is_valid = validate_combination(nums)
                    status_tag = " (✅ 統計解析室: 合格)" if is_valid else " (⚠️ 統計解析室: 境界外)"
                    line = f"{line}{status_tag}"
                except ValueError:
                    pass
        validated_lines.append(line)

    return "\n".join(validated_lines)