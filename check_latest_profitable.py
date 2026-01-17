from database_manager import DatabaseManager
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_profitable():
    db = DatabaseManager()
    response = db.supabase.table("products")\
        .select("title, price, ai_analysis, status")\
        .eq("status", "profitable")\
        .order("scraped_at", desc=True)\
        .limit(5)\
        .execute()
    
    if not response.data:
        print("有望な商品は見つかりませんでした。")
        return

    print(f"--- 最新の有望商品 ({len(response.data)}件) ---")
    for item in response.data:
        print(f"\n商品: {item['title']}")
        print(f"価格: ¥{item['price']:,}")
        ai = item.get('ai_analysis', {})
        print(f"価値ランク: {ai.get('investment_value')}")
        print(f"理由: {ai.get('trend_reason')}")

if __name__ == "__main__":
    check_profitable()

