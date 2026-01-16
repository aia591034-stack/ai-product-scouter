import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        self.supabase: Client = create_client(url, key)

    def get_active_search_configs(self):
        """有効な検索設定を取得する"""
        response = self.supabase.table("search_configs")\
            .select("*")\
            .eq("is_active", True)\
            .execute()
        return response.data

    def product_exists(self, platform: str, item_id: str) -> bool:
        """商品が既にDBに存在するかチェックする"""
        response = self.supabase.table("products")\
            .select("id")\
            .eq("platform", platform)\
            .eq("item_id", item_id)\
            .execute()
        return len(response.data) > 0

    def save_product(self, product_data: dict):
        """商品データを保存する"""
        try:
            # 重複チェック
            if self.product_exists(product_data['platform'], product_data['item_id']):
                print(f"Skipping existing item: {product_data['item_id']}")
                return None
            
            response = self.supabase.table("products").insert(product_data).execute()
            print(f"Saved item: {product_data['title'][:20]}...")
            return response.data
        except Exception as e:
            print(f"Error saving product: {e}")
            return None

    def get_new_products(self, limit=5):
        """分析待ち(status='new')の商品を取得する"""
        response = self.supabase.table("products")\
            .select("*")\
            .eq("status", "new")\
            .limit(limit)\
            .execute()
        return response.data

    def update_product_analysis(self, item_id, analysis_result, new_status):
        """分析結果とステータスを更新する"""
        try:
            self.supabase.table("products")\
                .update({
                    "ai_analysis": analysis_result,
                    "status": new_status
                })\
                .eq("id", item_id)\
                .execute()
            print(f"Updated product {item_id} status to {new_status}")
        except Exception as e:
            print(f"Error updating product: {e}")
