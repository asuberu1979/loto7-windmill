import pandas as pd
import numpy as np
from collections import Counter

CSV_FILE = "loto7_data.csv"

class Loto7Analyzer:
    def __init__(self, csv_file=CSV_FILE):
        self.df = pd.read_csv(csv_file)
        self.main_cols = [f"本数字{i}" for i in range(1, 8)]
        self.bonus_cols = ["ボーナス1", "ボーナス2"]
        
        # 数字を2桁文字列（01~37）から数値（1~37）扱いに揃える
        for col in self.main_cols + self.bonus_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors="coerce").astype("Int64")

    def get_recent_data(self, span=20):
        """直近span回のデータを取得"""
        return self.df.tail(span)

    def calculate_number_scores(self, span=20):
        """2〜4等狙いのための数字別スコアリング"""
        recent_df = self.get_recent_data(span)
        last_row = self.df.iloc[-1]
        
        # 直近の本数字・ボーナス数字を抽出
        last_mains = set(last_row[self.main_cols].dropna().values)
        last_bonuses = set(last_row[self.bonus_cols].dropna().values)
        
        scores = {n: 0.0 for n in range(1, 38)}

        # 1. 直近の出現頻度スコア (直近span回)
        recent_mains = recent_df[self.main_cols].values.flatten()
        freq = Counter(recent_mains)
        for num, count in freq.items():
            if pd.notna(num) and 1 <= num <= 37:
                scores[num] += count * 1.5

        # 2. 前回からの引っ張り数字（連足）加点
        for num in last_mains:
            if 1 <= num <= 37:
                scores[num] += 3.0

        # 3. 前回のボーナス数字からの流出（2等狙い重要指標）加点
        for num in last_bonuses:
            if 1 <= num <= 37:
                scores[num] += 2.5

        # スコア順にソート
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores

    def get_pairing_matrix(self, target_num):
        """特定数字と一緒に選ばれやすい相性パートナー数字を抽出"""
        all_mains = self.df[self.main_cols].values
        partners = []
        
        for row in all_mains:
            if target_num in row:
                partners.extend([n for n in row if n != target_num and pd.notna(n)])
                
        partner_counts = Counter(partners)
        return partner_counts.most_common(10)

    def is_valid_combination(self, combo):
        """2〜4等狙い用の健全性フィルター"""
        nums = sorted(combo)
        
        # 過去1等と完全一致は除外
        all_mains_tuples = set(tuple(sorted(row)) for row in self.df[self.main_cols].values)
        if tuple(nums) in all_mains_tuples:
            return False, "過去1等と完全一致"

        # 奇偶バランスチェック（全奇数・全偶数は排除）
        odds = sum(1 for n in nums if n % 2 != 0)
        if odds in [0, 7]:
            return False, "奇数偶数の偏りすぎ"

        # 合計値チェック（標準範囲 110〜160）
        total = sum(nums)
        if not (100 <= total <= 170):
            return False, f"合計値異常 ({total})"

        return True, "OK"

    def run_analysis(self):
        """分析の総合実行"""
        scores = self.calculate_number_scores(span=15)
        top_candidates = [n for n, score in scores[:12]]
        axis_candidates = [n for n, score in scores[:4]]
        
        print("=== 2〜4等狙い データ分析レポート ===")
        print(f"最新データ: 第{self.df.iloc[-1]['回数']}回 ({self.df.iloc[-1]['抽選日']})")
        print("\n【高確率 軸数字候補 (TOP4)】")
        for num, score in scores[:4]:
            print(f" 数字: {num:02d} | 分析スコア: {score:.1f}")

        print("\n【軸数字に対するベスト相性パートナー】")
        for axis in axis_candidates:
            partners = self.get_pairing_matrix(axis)
            p_str = ", ".join([f"{p[0]:02d}({p[1]}回)" for p in partners[:4]])
            print(f" 軸 [{axis:02d}] と相性が良い数字 -> {p_str}")

        print("\n【次回おすすめ高期待値ターゲット枠 (上位12選)】")
        print([f"{n:02d}" for n in top_candidates])

if __name__ == "__main__":
    analyzer = Loto7Analyzer()
    analyzer.run_analysis()