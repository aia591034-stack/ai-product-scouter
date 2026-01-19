import json
from database_manager import DatabaseManager

def inspect_analysis_data():
    db = DatabaseManager()
    # statusがprofitableなものを取得
    res = db.supabase.table("products").select("ai_analysis").eq("status", "profitable").limit(5).execute()
    
    print(f"取得件数: {len(res.data)}")
    
    for i, item in enumerate(res.data):
        ai = item.get('ai_analysis')
        print(f"\n--- Item {i+1} ---")
        print(f"Raw Type: {type(ai)}")
        print(f"Content: {ai}")
        
        if isinstance(ai, str):
            try:
                parsed = json.loads(ai)
                print(f"Parsed Genre: {parsed.get('genre')}")
            except Exception as e:
                print(f"JSON Parse Error: {e}")
        elif isinstance(ai, dict):
             print(f"Direct Genre: {ai.get('genre')}")

if __name__ == "__main__":
    inspect_analysis_data()

