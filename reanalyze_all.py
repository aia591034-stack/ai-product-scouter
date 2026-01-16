from database_manager import DatabaseManager

def reset_to_new():
    db = DatabaseManager()
    print("全商品のステータスを 'new' にリセットして、AIに再分析させます...")
    
    try:
        db.supabase.table("products")\
            .update({"status": "new", "ai_analysis": None})\
            .neq("id", "00000000-0000-0000-0000-000000000000")\
            .execute()
        print("リセット完了！ 'ai_analyzer.py' を実行してください。")
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    reset_to_new()

