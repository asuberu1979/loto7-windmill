import io
import pandas as pd
import requests

# mk-mode.com のロト7全データ静的CSV URL候補
CSV_URLS = [
    "https://www.mk-mode.com/rails/loto/LOTO7_ALL.csv",
    "https://www.mk-mode.com/rails/loto/loto7_all.csv",
    "https://www.mk-mode.com/rails/loto/LOTO7.csv",
]

CSV_FILE = "loto7_data.csv"


def fetch_loto7_csv():
    print("mk-mode.com から LOTO7_ALL.csv を直接取得中...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    df_raw = None
    successful_url = None

    for url in CSV_URLS:
        print(f"試行中: {url} ...", end=" ")
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                # 文字コード判定（UTF-8-SIG または Shift-JIS）
                content = res.content
                try:
                    text = content.decode("utf-8-sig")
                except UnicodeDecodeError:
                    text = content.decode("shift_jis", errors="ignore")

                df_raw = pd.read_csv(io.StringIO(text))
                if not df_raw.empty:
                    successful_url = url
                    print("-> 成功！")
                    break
            else:
                print(f"-> ステータス: {res.status_code}")
        except Exception as e:
            print(f"-> エラー: {e}")

    if df_raw is None:
        print("\n[エラー] CSVファイルの取得に失敗しました。")
        return None

    print(f"\n取得成功URL: {successful_url}")
    print(f"取得件数: {len(df_raw)}件")

    # 列名の自動マッピングと整形
    # mk-modeのCSV列名に対応
    cols = [str(c).strip() for c in df_raw.columns]
    df_raw.columns = cols

    # 回数・日付列の特定
    turn_col = next((c for c in cols if "回" in c or "turn" in c.lower()), cols[0])
    date_col = next((c for c in cols if "日" in c or "date" in c.lower()), cols[1] if len(cols) > 1 else "")

    # 本数字・ボーナス数字の抽出
    num_cols = [c for c in cols if c not in [turn_col, date_col]]

    records = []
    for _, row in df_raw.iterrows():
        times = row[turn_col]
        date = row[date_col] if date_col else ""

        # 行内の全数値（1〜37）を抽出
        nums = []
        for val in row[num_cols].values:
            try:
                n = int(val)
                if 1 <= n <= 37:
                    nums.append(str(n).zfill(2))
            except (ValueError, TypeError):
                continue

        if len(nums) >= 7:
            main_nums = nums[:7]
            bonus_nums = nums[7:9] if len(nums) >= 9 else (nums[7:8] if len(nums) >= 8 else ["", ""])
            b1 = bonus_nums[0] if len(bonus_nums) > 0 else ""
            b2 = bonus_nums[1] if len(bonus_nums) > 1 else ""

            records.append({
                "回数": times,
                "抽選日": str(date),
                "本数字1": main_nums[0],
                "本数字2": main_nums[1],
                "本数字3": main_nums[2],
                "本数字4": main_nums[3],
                "本数字5": main_nums[4],
                "本数字6": main_nums[5],
                "本数字7": main_nums[6],
                "ボーナス1": b1,
                "ボーナス2": b2,
            })

    df = pd.DataFrame(records)

    # 回数整形＆ソート
    df["回数"] = pd.to_numeric(df["回数"], errors="coerce")
    df = df.dropna(subset=["回数"]).drop_duplicates(subset=["回数"])
    df = df.sort_values(by="回数", ascending=True).reset_index(drop=True)
    df["回数"] = df["回数"].astype(int)

    # 保存
    df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
    print(f"\n成功: 全{len(df)}件のデータを '{CSV_FILE}' に保存しました！")
    print(f"取得範囲: 第{df['回数'].min()}回 〜 第{df['回数'].max()}回")

    print("\n【第1回〜第3回】")
    print(df.head(3).to_string(index=False))
    print("\n【最新3回】")
    print(df.tail(3).to_string(index=False))

    return df


if __name__ == "__main__":
    fetch_loto7_csv()