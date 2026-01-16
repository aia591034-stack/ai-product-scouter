import os
from dotenv import load_dotenv
from supabase import create_client, Client
import sys
import io

# 文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .envファイルを読み込み
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("エラー: .envファイルに SUPABASE_URL または SUPABASE_KEY が設定されていません。")
    sys.exit(1)

try:
    print("Supabaseへ接続中...")
    supabase: Client = create_client(url, key)
    
    # search_configs テーブルからデータを取得
    response = supabase.table("search_configs").select("*").execute()
    
    print("接続成功！")
    print(f"取得データ件数: {len(response.data)}")
    
    if len(response.data) > 0:
        print("--- データサンプル ---")
        for item in response.data:
            print(f"ID: {item['id']}")
            print(f"キーワード: {item['keyword']}")
            print(f"目標利益: {item['target_profit']}")
            print("-------------------")
    else:
        print("データは0件でした。")

except Exception as e:
    print(f"接続エラーが発生しました: {e}")
