import os
from database_manager import DatabaseManager
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def check_products():
    try:
        db = DatabaseManager()
        
        # 全商品数
        count_res = db.supabase.table("products").select("id", count="exact", head=True).execute()
        total_count = count_res.count
        print(f"商品データ総数: {total_count}")

        if total_count == 0:
            print("\n商品データが1件もありません。")
            print("解決策: スクレイピングを実行してデータを収集する必要があります。")
            return

        # ステータスごとの内訳
        status_res = db.supabase.table("products").select("status").execute()
        from collections import Counter
        statuses = [item.get('status', 'unknown') for item in status_res.data]
        counts = Counter(statuses)
        
        print("\nステータス内訳:")
        for status, count in counts.items():
            print(f" - {status}: {count}件")

        # 分析済みデータの確認
        analyzed_res = db.supabase.table("products").select("ai_analysis").neq("status", "new").limit(5).execute()
        analyzed_count = len(analyzed_res.data)
        
        if counts.get('new', 0) > 0 and analyzed_count == 0:
            print("\n商品はありますが、AI分析が行われていません。")
            print("解決策: AI分析プロセスを実行して、ジャンル情報を生成する必要があります。")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    check_products()
