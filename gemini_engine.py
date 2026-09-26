import os
import json
import time
from dotenv import load_dotenv, find_dotenv
from google import genai
from analyzer import Loto7Analyzer

def generate_predictions(analysis_summary=None, api_key=None):
    # 1. APIキーの取得
    if not api_key:
        load_dotenv(find_dotenv(usecwd=True))
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(".env ファイルまたは Streamlit Secrets に GEMINI_API_KEY が見つかりませんでした。")

    # Gemini クライアントの初期化
    client = genai.Client(api_key=api_key)

    # 2. analyzer.py から最新の分析データを取得
    analyzer = Loto7Analyzer()
    scores = analyzer.calculate_number_scores(span=15)
    
    top12 = [f"{n:02d}" for n, s in scores[:12]]
    axis4 = [f"{n:02d}" for n, s in scores[:4]]
    
    axis_partners = {}
    for axis in [n for n, s in scores[:4]]:
        partners = analyzer.get_pairing_matrix(axis)
        axis_partners[f"{axis:02d}"] = [f"{p[0]:02d}" for p in partners[:4]]

    last_row = analyzer.df.iloc[-1]
    last_issue = int(last_row["回数"])
    last_date = str(last_row["抽選日"])
    next_issue = last_issue + 1

    # 3. プロンプト作成
    prompt = f"""
あなたはロト7のデータ分析プロフェッショナルです。
提供された統計分析データをもとに、次回（第{next_issue}回）の「2〜4等当選」を狙うための最適化された【買い目5パターン】を提案してください。

### 【直近（第{last_issue}回: {last_date}）データ分析結果】
- 高期待値ターゲット12選: {', '.join(top12)}
- 高確率 軸数字 (TOP4): {', '.join(axis4)}
- 軸数字と相性が良いパートナー数字:
{json.dumps(axis_partners, ensure_ascii=False, indent=2)}

### 【購入組み合わせ選定条件】
1. **1口につき本数字7つ（01〜37）**を昇順で選定すること。
2. **2〜4等（5〜6数字一致）を分散して拾う**ため、口ごとに異なる軸数字や相性ペアを組み込み、全体のカバレッジを高めること。
3. **合計値フィルター**: 各口の7つの合計値が **110〜160** の範囲内になるよう調整すること。
4. **奇偶バランス**: 奇数と偶数の比率は **3:4** または **4:3** を推奨とし、全奇数・全偶数は排除すること。
5. **極端なパターンの排除**: 連続する数字は最大2〜3個までとし、過度な偏りを避けること。

### 【出力フォーマット】
以下の構成で分かりやすく回答してください。

1. **【第{next_issue}回 戦略方針】**
   - 今回の軸数字の振り分けと組み合わせの工夫

2. **【おすすめ買い目 5選】**
   - 第1口: [数字7つ] (軸: XX / 合計: XXX / 狙い)
   - 第2口: [数字7つ] (軸: XX / 合計: XXX / 狙い)
   - 第3口: [数字7つ] (軸: XX / 合計: XXX / 狙い)
   - 第4口: [数字7つ] (軸: XX / 合計: XXX / 狙い)
   - 第5口: [数字7つ] (軸: XX / 合計: XXX / 狙い)

3. **【立ち回り解説＆アドバイス】**
   - 今回選定した組み合わせの期待値とポイント
"""

    # 4. API呼び出し（503エラー対策のリトライ付き）
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Gemini API 送信中... (試行 {attempt}/{max_retries})")
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )

            output_filename = f"prediction_issue_{next_issue}.txt"
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(response.text)

            return response.text

        except Exception as e:
            if "503" in str(e) and attempt < max_retries:
                time.sleep(3)  # 503が出たら3秒待ってリトライ
                continue
            raise RuntimeError(f"Gemini API 呼び出しエラー: {e}")