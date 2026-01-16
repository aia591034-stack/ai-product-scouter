from playwright.sync_api import sync_playwright
import time
import sys
import io
import random
from database_manager import DatabaseManager

# 文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def parse_price(price_text):
    """¥4,999 などの文字列を整数 4999 に変換"""
    if not price_text:
        return 0
    clean_text = price_text.replace('¥', '').replace(',', '').replace(' ', '')
    try:
        return int(clean_text)
    except ValueError:
        return 0

def scrape_and_save():
    db = DatabaseManager()
    
    # 1. 監視設定を取得
    configs = db.get_active_search_configs()
    if not configs:
        print("有効な監視設定がありません。")
        return

    with sync_playwright() as p:
        # ブラウザ起動
        browser = p.chromium.launch(headless=True) # 本番はHeadlessでOK
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()

        for config in configs:
            keyword = config['keyword']
            print(f"\n--- Searching for: {keyword} ---")
            
            # URL構築 (新しい順で検索すると効率が良い)
            # sort=created_time, order=desc
            url = f"https://jp.mercari.com/search?keyword={keyword}&sort=created_time&order=desc"
            
            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(5000 + random.randint(1000, 3000)) # ランダム待機
                
                # 商品リストを取得
                items = page.locator('li[data-testid="item-cell"]')
                count = items.count()
                print(f"Found {count} items.")
                
                # 上位10件のみ処理（頻繁に実行する前提）
                process_count = min(count, 10)
                
                for i in range(process_count):
                    item = items.nth(i)
                    try:
                        # リンク取得
                        link_element = item.locator('a').first
                        item_url = "https://jp.mercari.com" + link_element.get_attribute('href')
                        
                        # ID抽出 (URLから /item/m123456... を抽出)
                        item_id = item_url.split('/item/')[-1]
                        
                        # すでにDBにあるかチェック（詳細ページに行く前にチェックして効率化）
                        if db.product_exists('mercari', item_id):
                            print(f"Skipping known item: {item_id}")
                            continue

                        # 情報抽出
                        img = item.locator('img').first
                        title = img.get_attribute('alt') if img.count() > 0 else "No Title"
                        image_url = img.get_attribute('src') if img.count() > 0 else ""
                        
                        price_element = item.locator('span').filter(has_text="¥")
                        price_text = price_element.first.inner_text() if price_element.count() > 0 else "0"
                        price = parse_price(price_text)

                        # 価格取得エラー(0円)の場合はスキップ
                        if price == 0:
                            print(f"Skipping item with 0 price (parse error): {item_id}")
                            continue

                        # データ構築
                        product_data = {
                            "platform": "mercari",
                            "item_id": item_id,
                            "title": title,
                            "price": price,
                            "image_url": image_url,
                            "product_url": item_url,
                            "status": "new" # 未分析状態
                        }
                        
                        # DB保存
                        db.save_product(product_data)
                        
                        # スクレイピングマナーのための待機
                        time.sleep(1)

                    except Exception as e:
                        print(f"Error processing item {i}: {e}")
                        continue

            except Exception as e:
                print(f"Error scraping {keyword}: {e}")
            
        browser.close()

if __name__ == "__main__":
    scrape_and_save()
