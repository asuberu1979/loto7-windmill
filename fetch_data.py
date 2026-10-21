"""
ロト7 過去データの取得・保存

mk-mode.com の静的CSVを取得して loto7_data.csv に保存します。
  - 取得したデータは検証してから保存します(件数・連番・数字の範囲)。
    問題があれば、既存のファイルは上書きしません。
  - 取得できない / 検証に通らない場合は、保存済みのCSVを使います。
    そのときは返り値の df.attrs["stale"] が True になります。
  - 保存は一時ファイルに書いてから置き換えるので、途中で失敗しても元のファイルは壊れません。
"""

import io
import os

import pandas as pd
import requests

# mk-mode.com のロト7全データ静的CSV URL候補
CSV_URLS = [
    "https://www.mk-mode.com/rails/loto/LOTO7_ALL.csv",
    "https://www.mk-mode.com/rails/loto/loto7_all.csv",
    "https://www.mk-mode.com/rails/loto/LOTO7.csv",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "loto7_data.csv")

MAIN_COLS = [f"本数字{i}" for i in range(1, 8)]
BONUS_COLS = ["ボーナス1", "ボーナス2"]
MIN_ROWS = 100   # これより少ない件数は異常とみなす

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def _fetch_remote():
    """mk-mode.com からCSVを取得して整形したDataFrameを返す。失敗したらNone。保存はしない。"""
    print("mk-mode.com から LOTO7_ALL.csv を直接取得中...")

    df_raw = None
    successful_url = None

    for url in CSV_URLS:
        print(f"試行中: {url} ...", end=" ")
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
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

    if df_raw is None or df_raw.empty:
        print("\n[警告] CSVファイルの取得に失敗しました。")
        return None

    print(f"\n取得成功URL: {successful_url}")
    print(f"取得件数: {len(df_raw)}件")

    # 列名の自動マッピングと整形
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
    if df.empty or "回数" not in df.columns:
        print("[警告] 取得したCSVから有効な行を読み取れませんでした。")
        return None

    # 回数整形＆ソート
    df["回数"] = pd.to_numeric(df["回数"], errors="coerce")
    df = df.dropna(subset=["回数"]).drop_duplicates(subset=["回数"])
    df = df.sort_values(by="回数", ascending=True).reset_index(drop=True)
    df["回数"] = df["回数"].astype(int)
    return df


def _validate(df, local):
    """取得データを保存してよいか検証する。戻り値: (OKか, 理由)"""
    need = ["回数", "抽選日"] + MAIN_COLS + BONUS_COLS
    missing = [c for c in need if c not in df.columns]
    if missing:
        return False, f"列が不足しています: {missing}"
    if len(df) < MIN_ROWS:
        return False, f"件数が少なすぎます({len(df)}件)"
    if local is not None and len(df) < len(local):
        return False, f"保存済みより件数が少ないです({len(df)}件 < {len(local)}件)"

    first, last = int(df["回数"].min()), int(df["回数"].max())
    if list(df["回数"]) != list(range(first, last + 1)):
        return False, "回数が連番になっていません"

    for _, row in df.iterrows():
        try:
            nums = [int(row[c]) for c in MAIN_COLS]
            bonus = [int(row[c]) for c in BONUS_COLS]
        except (ValueError, TypeError):
            return False, f"第{row['回数']}回の数字(本数字・ボーナス)を数値として読めません"
        if len(set(nums)) != 7 or any(not 1 <= n <= 37 for n in nums):
            return False, f"第{row['回数']}回の本数字が不正です: {nums}"
        if len(set(nums + bonus)) != 9 or any(not 1 <= n <= 37 for n in bonus):
            return False, f"第{row['回数']}回のボーナス数字が不正です: {bonus}"
    return True, "OK"


def _load_local():
    """保存済みCSVを、取得直後と同じ形(番号は文字列、回数は整数)で読む。なければNone。"""
    if not os.path.exists(CSV_FILE):
        return None
    try:
        df = pd.read_csv(CSV_FILE, encoding="utf-8-sig", dtype=str)
        df["回数"] = df["回数"].astype(int)
        return df
    except Exception as e:
        print(f"[警告] 保存済みCSVを読み込めませんでした: {e}")
        return None


def _save_atomic(df):
    tmp = CSV_FILE + ".tmp"
    df.to_csv(tmp, index=False, encoding="utf-8-sig")
    os.replace(tmp, CSV_FILE)


def fetch_data():
    local = _load_local()
    remote = _fetch_remote()

    if remote is not None:
        ok, reason = _validate(remote, local)
        if ok:
            try:
                _save_atomic(remote)
                print(f"\n成功: 全{len(remote)}件のデータを '{os.path.basename(CSV_FILE)}' に保存しました！")
            except OSError as e:
                print(f"[警告] CSVを保存できませんでした(取得したデータはこのまま使います): {e}")
            print(f"取得範囲: 第{remote['回数'].min()}回 〜 第{remote['回数'].max()}回")
            return remote
        print(f"[警告] 取得したデータが検証を通りませんでした: {reason}")

    if local is not None:
        print(f"[警告] 保存済みのデータ(第{int(local['回数'].max())}回まで)を使います。")
        local.attrs["stale"] = True
        return local

    print("[エラー] データを取得できず、保存済みのデータもありません。")
    return None


if __name__ == "__main__":
    fetch_data()
