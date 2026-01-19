from database_manager import DatabaseManager

def reset_analysis_status():
    db = DatabaseManager()
    
    print("分析済みデータのステータスを 'new' にリセットします...")
    
    # statusが 'profitable' または 'discarded' のものを対象にする
    # SupabaseのPythonクライアントでOR条件が複雑なため、単純に全件更新を試みるか、分けて実行
    
    try:
        # profitable -> new
        res1 = db.supabase.table("products").update({"status": "new", "ai_analysis": None}).eq("status", "profitable").execute()
        print(f"Reset {len(res1.data)} profitable items.")
        
        # discarded -> new (必要であれば)
        res2 = db.supabase.table("products").update({"status": "new", "ai_analysis": None}).eq("status", "discarded").execute()
        print(f"Reset {len(res2.data)} discarded items.")
        
        print("リセット完了。スクレイピング済みとして再度分析待ちになりました。")
        
    except Exception as e:
        print(f"Error resetting data: {e}")

if __name__ == "__main__":
    reset_analysis_status()
