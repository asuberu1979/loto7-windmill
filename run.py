import os
from dotenv import load_dotenv
from gemini_engine import generate_predictions

# .env ファイルから GEMINI_API_KEY を読み込み
load_dotenv()

def main():
    print("=" * 50)
    print(" 🎯 ロト7 AI予測を生成中... (Gemini API)")
    print("=" * 50)
    
    try:
        # 予測処理を実行
        result = generate_predictions()
        
        print("\n【 予測結果 】\n")
        print(result)
        print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()