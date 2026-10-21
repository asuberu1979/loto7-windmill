"""
PROJECT WINDMILL - ロト7 組み合わせ生成エンジン (Pure Python / API不使用)

やっていること:
  1. 直近の本数字の出現回数で、1〜37を「出ていない数字(cold)」「中間」
     「よく出ている数字(hot)」に分ける
  2. cold / 中間 / hot から1つずつ「軸数字」をランダムに選ぶ
  3. 軸を含む組み合わせをランダムに作り、条件フィルター(合計・奇偶・連続・高低)を
     通ったものを5つ採用する

重要:
  ロト7の抽せんは毎回独立で、どの7数字の組み合わせも当せん確率は同じです。
  軸の選び方も条件フィルターも、当せん確率を変えるものではありません。
  エンタメ用の生成器です。
"""

import random

from fetch_data import fetch_data

MAIN_COLS = [f"本数字{i}" for i in range(1, 8)]

RECENT_DRAWS = 10      # 軸の候補を決めるときに見る直近の回数
NUM_TICKETS = 5        # 生成する買い目の数
AXIS_RETRIES = 50      # 軸が条件に合わず買い目を作れなかったときの選び直し上限
MAX_ATTEMPTS = 5000    # 1組の軸あたりの組み合わせ生成の試行上限

SUM_RANGE = (90, 170)
RATIOS = [(3, 4), (4, 3), (2, 5), (5, 2)]
HIGH_LOW_THRESHOLD = 19
MAX_CONSECUTIVE = 2


# ==========================================
# 条件フィルター
# ==========================================
def is_sum_in_range(numbers, min_sum=SUM_RANGE[0], max_sum=SUM_RANGE[1]):
    return min_sum <= sum(numbers) <= max_sum


def is_odd_even_balanced(numbers, allowed_ratios=RATIOS):
    odd_count = sum(1 for x in numbers if x % 2 != 0)
    return (odd_count, 7 - odd_count) in allowed_ratios


def is_consecutive_valid(numbers, max_consecutive=MAX_CONSECUTIVE):
    sorted_nums = sorted(numbers)
    consecutive_count = 0
    max_count = 0
    for i in range(len(sorted_nums) - 1):
        if sorted_nums[i + 1] == sorted_nums[i] + 1:
            consecutive_count += 1
            max_count = max(max_count, consecutive_count)
        else:
            consecutive_count = 0
    return max_count < max_consecutive


def is_high_low_balanced(numbers, threshold=HIGH_LOW_THRESHOLD, allowed_ratios=RATIOS):
    low_count = sum(1 for x in numbers if x < threshold)
    return (low_count, 7 - low_count) in allowed_ratios


def validate_combination(numbers):
    if len(numbers) != 7 or len(set(numbers)) != 7:
        return False
    return (
        is_sum_in_range(numbers)
        and is_odd_even_balanced(numbers)
        and is_consecutive_valid(numbers)
        and is_high_low_balanced(numbers)
    )


# ==========================================
# 軸数字の選定
# ==========================================
def _main_numbers(row):
    """1行から本数字(1〜37)を取り出す。番号が文字列('07')でも整数でも読める。"""
    nums = []
    for col in MAIN_COLS:
        try:
            n = int(row[col])
        except (KeyError, ValueError, TypeError):
            continue
        if 1 <= n <= 37:
            nums.append(n)
    return nums


def classify_numbers(df, rng=random):
    """直近の出現回数で 1〜37 を cold(10) / mid(17) / hot(10) に分ける。

    出現回数が同じ数字は、先にシャッフルしてから並べ替えることで、
    小さい数字や大きい数字が有利にならないようにしている。
    """
    freq = {n: 0 for n in range(1, 38)}
    for _, row in df.tail(RECENT_DRAWS).iterrows():
        for n in _main_numbers(row):
            freq[n] += 1
    shuffled = rng.sample(range(1, 38), 37)
    ranked = sorted(shuffled, key=lambda n: freq[n])   # 出現の少ない順(同率はランダム)
    return freq, sorted(ranked[:10]), sorted(ranked[10:-10]), sorted(ranked[-10:])


def generate_combinations(axes, rng=random, n=NUM_TICKETS, max_attempts=MAX_ATTEMPTS):
    """軸を含む組み合わせをランダムに作り、条件フィルターを通ったものを最大n個返す。"""
    pool = [x for x in range(1, 38) if x not in axes]
    found = []
    for _ in range(max_attempts):
        if len(found) >= n:
            break
        cand = sorted(list(axes) + rng.sample(pool, 7 - len(axes)))
        if validate_combination(cand) and cand not in found:
            found.append(cand)
    return found


def _fmt(nums):
    return ", ".join(f"{n:02d}" for n in nums)


# ==========================================
# レポート生成
# ==========================================
def generate_predictions(df=None, rng=None):
    rng = rng or random

    if df is None or (hasattr(df, "empty") and df.empty):
        df = fetch_data()
    if df is None or (hasattr(df, "empty") and df.empty):
        return "⚠️ 過去データを取得できませんでした。"

    freq, cold, mid, hot = classify_numbers(df, rng)

    combos = []
    axis_cold = axis_mid = axis_hot = None
    for _ in range(AXIS_RETRIES):
        axis_cold, axis_mid, axis_hot = rng.choice(cold), rng.choice(mid), rng.choice(hot)
        axes = sorted([axis_cold, axis_mid, axis_hot])
        combos = generate_combinations(axes, rng)
        if len(combos) >= NUM_TICKETS:
            break
    else:
        return "⚠️ 条件を満たす組み合わせを作れませんでした。もう一度お試しください。"

    if "回数" in df.columns:
        last_draw = int(df["回数"].max())
        recent = df.tail(RECENT_DRAWS)
        range_text = f"(第{int(recent['回数'].min())}〜第{int(recent['回数'].max())}回)"
    else:
        last_draw = len(df)
        range_text = ""
    next_draw = last_draw + 1
    stale = bool(getattr(df, "attrs", {}).get("stale"))

    lines = []
    add = lines.append
    add(f"# PROJECT WINDMILL - 第{next_draw}回 組み合わせ生成レポート\n")
    add("> エンタメ用の生成レポートです。ロト7は毎回独立した抽せんで、どの7数字の組み合わせも当せん確率は同じです。")
    add("> 軸数字の選び方も条件フィルターも、当せん確率を変えるものではありません。\n")
    if stale:
        add(f"⚠️ 最新データを取得できなかったため、保存済みのデータ(第{last_draw}回まで)で生成しています。\n")

    add("## 1. 軸数字の選定\n")
    add(f"直近{RECENT_DRAWS}回{range_text}の本数字の出現回数で、1〜37を3つのグループに分けました"
        "(出現回数が同じ数字は、順序をランダムに決めています)。\n")
    add(f"- 出現の少ない数字 (cold・{len(cold)}個): {_fmt(cold)}")
    add(f"- 中間の数字 (mid・{len(mid)}個): {_fmt(mid)}")
    add(f"- よく出ている数字 (hot・{len(hot)}個): {_fmt(hot)}")
    add(f"- 今回の軸: cold側 `{axis_cold:02d}` / 中間 `{axis_mid:02d}` / hot側 `{axis_hot:02d}` "
        "(各グループからランダムに1つずつ)\n")

    add("## 2. 条件フィルターの確認\n")
    add(f"| № | 合計 ({SUM_RANGE[0]}〜{SUM_RANGE[1]}) | 奇偶 | 連続番号 | 高低 (1-18 / 19-37) | 判定 |")
    add("|---|---|---|---|---|---|")
    for i, comb in enumerate(combos, 1):
        total = sum(comb)
        odd_c = sum(1 for x in comb if x % 2 != 0)
        low_c = sum(1 for x in comb if x < HIGH_LOW_THRESHOLD)
        has_pair = any(b == a + 1 for a, b in zip(comb, comb[1:]))
        add(f"| {i} | {total} ✅ | 奇{odd_c}:偶{7 - odd_c} ✅ | {'2連あり' if has_pair else 'なし'} ✅ "
            f"| 低{low_c}:高{7 - low_c} ✅ | **条件クリア** |")
    add("")
    add(f"条件: 合計{SUM_RANGE[0]}〜{SUM_RANGE[1]} / 奇偶比 3:4・4:3・2:5・5:2 / 連続番号は2連まで / "
        "高低比 3:4・4:3・2:5・5:2")
    add("5つの買い目はすべて、上の3つの軸数字を含んでいます。\n")

    add("## 3. 買い目\n")
    for i, comb in enumerate(combos, 1):
        add(f"- 買い目{i}: [{_fmt(comb)}]")
    add("\n確率の風車は気まぐれに回ります。購入は無理のない範囲で、お楽しみ程度にどうぞ。")

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_predictions())
