from combo_engine import generate_predictions


def main():
    print("=" * 50)
    print(" 🎯 ロト7 組み合わせ生成 (Pure Python / API不使用)")
    print("=" * 50)

    try:
        result = generate_predictions()

        print("\n【 生成結果 】\n")
        print(result)
        print("\n" + "=" * 50)

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
