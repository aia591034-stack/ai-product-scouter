import feedparser
import requests
from database_manager import DatabaseManager
import sys
import io

# 文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fetch_and_add_trends():
    print("Google Trendsから急上昇ワードを取得中...")
    
    # Google Trends RSS (URLを.comに変更し、User-Agentを設定)
    rss_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=JP"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(rss_url, headers=headers)
        if response.status_code != 200:
            print(f"エラー: Google Trendsへのアクセスに失敗しました (Status: {response.status_code})")
            return
            
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"通信エラー: {e}")
        return
    
    db = DatabaseManager()
    added_count = 0
    
    if not feed.entries:
        print("トレンドの取得に失敗しました。")
        return

    print(f"取得したトレンド数: {len(feed.entries)}件")

    for entry in feed.entries[:5]: # 上位5件のみ（多すぎるとノイズになるため）
        keyword = entry.title
        traffic = entry.get('ht_approx_traffic', 'N/A')
        
        print(f"チェック中: {keyword} (検索数: {traffic})")
        
        # 既に登録済みかチェック（簡易的：search_configsテーブルをキーワードで検索）
        # ※DatabaseManagerにメソッドがないので、ここで直接クエリ
        try:
            existing = db.supabase.table("search_configs")\
                .select("id")\
                .eq("keyword", keyword)\
                .execute()
            
            if len(existing.data) == 0:
                # 新規登録
                db.supabase.table("search_configs").insert({
                    "keyword": keyword,
                    "target_profit": 3000, # 仮の設定
                    "is_active": True
                }).execute()
                print(f"  -> 追加しました: {keyword}")
                added_count += 1
            else:
                print("  -> 既に登録済みです")
                
        except Exception as e:
            print(f"  -> エラー: {e}")

    print(f"処理完了。新規追加: {added_count}件")

if __name__ == "__main__":
    fetch_and_add_trends()
