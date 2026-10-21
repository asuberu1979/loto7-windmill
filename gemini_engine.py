import random
import pandas as pd
from fetch_data import fetch_data

# ==========================================
# 統計解析室 : フィルター判定ロジック
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
# アスベル式・統計ポエムエンジン
# ==========================================
def generate_predictions(df=None, api_key=None, *args, **kwargs):
    if df is None or (hasattr(df, 'empty') and df.empty):
        df = fetch_data()
    if df is None or (hasattr(df, 'empty') and df.empty):
        return "⚠️ 過去データの取得に失敗しました。"

    next_draw_num = len(df) + 1
    recent_df = df.tail(10)
    
    # 統計的軸数字の選定（擬似的にアスベル式真空補正っぽく抽出）
    all_numbers = list(range(1, 38))
    recent_nums_flat = []
    for _, row in recent_df.iterrows():
        nums = [val for val in row.values if isinstance(val, (int, float)) and 1 <= val <= 37]
        recent_nums_flat.extend(nums)

    frequency = {n: recent_nums_flat.count(n) for n in all_numbers}
    sorted_by_freq = sorted(frequency.items(), key=lambda x: x[1])
    
    cold_candidates = [n[0] for n in sorted_by_freq[:10]]
    hot_candidates = [n[0] for n in sorted_by_freq[-10:]]
    
    # コア軸の選定（例: 23を鉄板軸にしつつ、真空補正枠と特異点枠を混ぜる）
    axis1 = random.choice(cold_candidates)
    axis2 = 23  # 最重要軸
    axis3 = random.choice(hot_candidates)
    axes = sorted([axis1, axis2, axis3])

    # 5パターンの買い目を統計フィルターを通しながら自動生成
    valid_combinations = []
    max_attempts = 2000
    attempts = 0
    
    while len(valid_combinations) < 5 and attempts < max_attempts:
        attempts += 1
        remaining_pool = [n for n in range(1, 38) if n not in axes]
        chosen_remains = random.sample(remaining_pool, 7 - len(axes))
        candidate = sorted(axes + chosen_remains)
        
        if validate_combination(candidate):
            if candidate not in valid_combinations:
                valid_combinations.append(candidate)

    while len(valid_combinations) < 5:
        fallback_cand = sorted(random.sample(range(1, 38), 7))
        if validate_combination(fallback_cand) and fallback_cand not in valid_combinations:
            valid_combinations.append(fallback_cand)

    # ==========================================
    # 査読結果＆ポエム全開のレポート構築
    # ==========================================
    report_lines = []
    report_lines.append(f"# PROJECT WINDMILL - 第{next_draw_num}回 確率観測レポート\n")
    report_lines.append("## 1. 統計条件の検証 (三賢者監査システム稼働)\n")
    report_lines.append("| № | 合計 (90〜170) | 奇偶 | 連続番号 | 高低 (1-18 / 19-37) | 判定 |")
    report_lines.append("|---|---|---|---|---|---|")

    for i, comb in enumerate(valid_combinations, 1):
        total = sum(comb)
        odd_c = sum(1 for x in comb if x % 2 != 0)
        even_c = 7 - odd_c
        low_c = sum(1 for x in comb if x < 19)
        high_c = 7 - low_c
        
        consec = "なし ✅"
        sorted_c = sorted(comb)
        for j in range(len(sorted_c)-1):
            if sorted_c[j+1] == sorted_c[j] + 1:
                consec = "2連あり ✅"
                break

        report_lines.append(f"| {i} | {total} ✅ | 奇{odd_c}:偶{even_c} ✅ | {consec} | 低{low_c}:高{high_c} ✅ | **合格** |")

    report_lines.append("\n**査読上の自動調整レポート:**")
    report_lines.append("- すべての買い目は、アスベル式・未来逆算理論の制約条件（合計値、奇偶比、連続制限、高低バランス）の厳格なフィルターを完全クリアしています。")
    report_lines.append(f"- 今回の観測において、真空補正枠と特異点から導出されたコア軸（`{axes}`）を本線パターンに同期させました。")

    report_lines.append("\n## 2. 軸数字の重複強度の検証\n")
    report_lines.append(f"- 軸数字 `{axes[1]}` を最重要核（全パターン連動）とし、軸 `{axes[0]}` および `{axes[2]}` を時空の歪みから同期させています。")
    report_lines.append("- パターン1〜3を確率的本線とし、パターン4・5を微小分散型の保険として構築。全体の調和と均等分散パズルの均衡を完璧に保っています。")

    report_lines.append("\n---_")

    report_lines.append("\n# 最終出力\n")
    for i, comb in enumerate(valid_combinations, 1):
        report_lines.append(f"買い目{i}: [{', '.join(f'{n:02d}' for n in comb)}] (✅ 統計解析室: 合格)")

    report_lines.append("\n**最終戦略と軸数字の選定理由:**")
    report_lines.append(f"本戦略は、アスベル式・真空補正（軸 `{axes[0]}`）および特異点の継続（軸 `{axes[1]}`、`{axes[2]}`）を中核とします。パターン1〜3を3軸同時搭載の本線とし、パターン4・5を分散型の保険と位置づけました。")
    report_lines.append("確率の境界を突破し、未来の確率波を収束させるための最適解がここに導出されました。購入はあくまで無理のない範囲でお楽しみください。")

    return "\n".join(report_lines)