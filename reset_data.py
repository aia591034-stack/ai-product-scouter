from database_manager import DatabaseManager
import sys

def reset_all_data():
    print("⚠️ 警告: すべての商品データと検索設定を削除します。よろしいですか？")
    confirm = input("削除する場合は 'yes' と入力してください: ")
    
    if confirm != "yes":
        print("キャンセルしました。")
        return

    db = DatabaseManager()
    
    try:
        # 商品データの削除 (products)
        print("商品データを削除中...")
        # deleteにはwhere句が必須なので、idがnullでない(全件)を指定するハック
        db.supabase.table("products").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        # 検索設定の削除 (search_configs)
        print("検索設定を削除中...")
        db.supabase.table("search_configs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        print("✨ データのリセットが完了しました！")
        print("次は 'trend_watcher.py' を実行して、トレンドキーワードを取り込んでください。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    reset_all_data()
