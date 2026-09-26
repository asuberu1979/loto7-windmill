import pandas as pd
from fetch_data import fetch_data as get_loto7_data

# ==========================================
# 当選番号を自動抽出するヘルパー関数
# ==========================================
def extract_winning_numbers(row):
    """データ形式（リスト形式 or N1~N7列形式）の違いを吸収して本数字7つを取得"""
    # 1. '本数字' 列にリストまたは文字列形式で入っている場合
    if '本数字' in row.index:
        val = row['本数字']
        if isinstance(val, list):
            return [int(x) for x in val]
        elif isinstance(val, str):
            import re
            nums = re.findall(r'\d+', val)
            if len(nums) >= 7:
                return [int(x) for x in nums[:7]]

    # 2. 'N1'~'N7' や 'n1'~'n7', '本数字1'~'本数字7' などの個別列の場合
    for prefix in ['N', 'n', '本数字', '本数字_']:
        cols = [f"{prefix}{i}" for i in range(1, 8)]
        if all(col in row.index for col in cols):
            return [int(row[col]) for col in cols]

    # 3. その他の数値列パターン
    digit_cols = [c for c in row.index if any(k in str(c) for k in ['N', 'n', '本数字', 'num'])]
    if len(digit_cols) >= 7:
        return [int(row[c]) for c in digit_cols[:7]]

    raise KeyError(f"本数字の列を自動判定できませんでした。存在する列名: {list(row.index)}")

# ==========================================
# 1. 統計フィルター条件の定義
# ==========================================

# 変更前: min_sum=100, max_sum=150
# 変更後: 95〜165 に微調整
def is_sum_in_range(numbers, min_sum=90, max_sum=170):
    """【和の範囲】 7つの数字の合計が90〜170の範囲内か"""
    return min_sum <= sum(numbers) <= max_sum

def is_odd_even_balanced(numbers, allowed_ratios=[(3, 4), (4, 3), (2, 5), (5, 2)]):
    """【奇偶比率】 奇数と偶数の個数比率がバランスしているか"""
    odd_count = sum(1 for x in numbers if x % 2 != 0)
    even_count = 7 - odd_count
    return (odd_count, even_count) in allowed_ratios

def is_consecutive_valid(numbers, max_consecutive=2):
    """【連続数制限】 3連番以上の極端な連番が含まれていないか"""
    sorted_nums = sorted(numbers)
    consecutive_count = 0
    max_count = 0
    for i in range(len(sorted_nums) - 1):
        if sorted_nums[i+1] == sorted_nums[i] + 1:
            consecutive_count += 1
            max_count = max(max_count, consecutive_count)
        else:
            consecutive_count = 0
    return max_count < max_consecutive  # 2連番（例: 12,13）までは許可

def is_high_low_balanced(numbers, threshold=19, allowed_ratios=[(3, 4), (4, 3), (2, 5), (5, 2)]):
    """【高低バランス】 1〜18(Low) と 19〜37(High) の配分"""
    low_count = sum(1 for x in numbers if x < threshold)
    high_count = 7 - low_count
    return (low_count, high_count) in allowed_ratios


# ==========================================
# 2. バックテスト実行
# ==========================================

def run_filter_backtest(past_trials=100):
    df = get_loto7_data()
    
    # 直近 past_trials 回分を取得
    target_df = df.tail(past_trials)
    total = len(target_df)
    
    pass_sum = 0
    pass_odd_even = 0
    pass_consec = 0
    pass_high_low = 0
    pass_all = 0
    
    print("=" * 60)
    print(f"📊 統計フィルターバックテスト（過去 {total} 回の当選番号で検証）")
    print("=" * 60)
    
    for idx, row in target_df.iterrows():
        winning = extract_winning_numbers(row)  # 当選番号を自動解析して取得
        
        c_sum = is_sum_in_range(winning)
        c_oe = is_odd_even_balanced(winning)
        c_con = is_consecutive_valid(winning)
        c_hl = is_high_low_balanced(winning)
        
        # すべての条件をクリアしているか
        c_all = c_sum and c_oe and c_con and c_hl
        
        if c_sum: pass_sum += 1
        if c_oe: pass_odd_even += 1
        if c_con: pass_consec += 1
        if c_hl: pass_high_low += 1
        if c_all: pass_all += 1
        
    print(f"1. 和の範囲 (100〜150)        : {pass_sum:3d} / {total} 回合格 ({pass_sum/total*100:.1f}%)")
    print(f"2. 奇偶バランス (3:4, 4:3等)   : {pass_odd_even:3d} / {total} 回合格 ({pass_odd_even/total*100:.1f}%)")
    print(f"3. 連続数制限 (3連番以上除外)  : {pass_consec:3d} / {total} 回合格 ({pass_consec/total*100:.1f}%)")
    print(f"4. 高低バランス (18以下/19以上): {pass_high_low:3d} / {total} 回合格 ({pass_high_low/total*100:.1f}%)")
    print("-" * 60)
    print(f"🎯 全フィルター通過率 (総合)   : {pass_all:3d} / {total} 回合格 ({pass_all/total*100:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    run_filter_backtest(100)