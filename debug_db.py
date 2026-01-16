from database_manager import DatabaseManager
import pandas as pd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def debug_db_status():
    db = DatabaseManager()
    
    # 全件取得
    response = db.supabase.table("products").select("status, price").execute()
    df = pd.DataFrame(response.data)
    
    if df.empty:
        print("DBは空です。")
        return

    print("--- DB保存状況の統計 ---")
    print(df['status'].value_counts())
    
    print("\n--- 価格0円のデータ数 ---")
    print(f"価格0円: {len(df[df['price'] == 0])}件")
    print(f"有効な価格: {len(df[df['price'] > 0])}件")

if __name__ == "__main__":
    debug_db_status()

