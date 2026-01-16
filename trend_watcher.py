from pytrends.request import TrendReq
from database_manager import DatabaseManager
import sys
import io
import time

# 文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fetch_and_add_trends():
    print("Google Trendsから急上昇ワードを取得中 (pytrends使用)...")
    
    try:
        # Google Trendsに接続 (hl=言語, tz=タイムゾーン)
        pytrends = TrendReq(hl='ja-JP', tz=540)
        
        # 今日の急上昇ワードを取得 (pn=国名)
        df = pytrends.trending_searches(pn='japan')
        
        if df.empty:
            print("トレンドの取得に失敗しました。")
            return
            
        trends = df[0].tolist()
        print(f"取得したトレンド数: {len(trends)}件")

        db = DatabaseManager()
        added_count = 0

        # 上位5件を処理
        for keyword in trends[:5]:
            print(f"チェック中: {keyword}")
            
            try:
                # 既に登録済みかチェック
                existing = db.supabase.table("search_configs")\
                    .select("id")\
                    .eq("keyword", keyword)\
                    .execute()
                
                if len(existing.data) == 0:
                    # 新規登録
                    db.supabase.table("search_configs").insert({
                        "keyword": keyword,
                        "target_profit": 3000,
                        "is_active": True
                    }).execute()
                    print(f"  -> 追加しました: {keyword}")
                    added_count += 1
                else:
                    print("  -> 既に登録済みです")
                    
            except Exception as e:
                print(f"  -> DBエラー: {e}")
            
            # API制限に配慮
            time.sleep(1)

        print(f"処理完了。新規追加: {added_count}件")

    except Exception as e:
        print(f"pytrendsエラー: {e}")

if __name__ == "__main__":
    fetch_and_add_trends()