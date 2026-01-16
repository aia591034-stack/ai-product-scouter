import requests
import feedparser
import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from database_manager import DatabaseManager
import sys
import io
import time

# 文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def fetch_and_add_trends():
    print("最新ニュースからトレンドを分析中...")
    
    # 複数のRSSソースからニュースを取得（安定性重視）
    rss_urls = [
        "https://news.yahoo.co.jp/rss/categories/business.xml",
        "https://news.yahoo.co.jp/rss/categories/it.xml",
        "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
    ]
    
    headlines = []
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                headlines.append(entry.title)
        except Exception as e:
            print(f"RSS取得エラー ({url}): {e}")

    if not headlines:
        print("ニュース記事を取得できませんでした。")
        return

    # Geminiにトレンドワードを抽出させる
    prompt = f"""
    以下の最新ニュースの見出しを読み、現在日本で注目が集まっており、
    メルカリなどのフリマサイトで「価格が高騰しそう」または「需要が急増しそう」な
    具体的な商品名やキーワードを5つ抽出してください。
    
    【ニュース見出し】
    {chr(10).join(headlines)}
    
    【回答ルール】
    ・具体的な固有名詞（商品名、キャラクター名、ブランド名、イベント名）を出すこと。
    ・「設定」や「ニュース」などの一般用語は除外。
    ・1行に1キーワード、合計5つ。解説は不要。
    """

    try:
        response = model.generate_content(prompt)
        # 行ごとに分割し、数字・記号・空白を徹底的に除去
        raw_lines = response.text.strip().split('\n')
        ai_keywords = []
        for line in raw_lines:
            # 先頭の数字とドット(1. )、ハイフン(- )、中黒(・)などを置換
            k = re.sub(r'^[0-9]+[\.\s、]+', '', line.strip()) # "1. " や "1 " を削除
            k = k.replace('・', '').replace('- ', '').strip()
            if k:
                ai_keywords.append(k)
        
        print(f"AIが予測したトレンドワード: {ai_keywords}")

        db = DatabaseManager()
        added_count = 0

        for keyword in ai_keywords[:5]:
            if len(keyword) < 2: continue
            
            print(f"チェック中: {keyword}")
            try:
                existing = db.supabase.table("search_configs").select("id").eq("keyword", keyword).execute()
                if len(existing.data) == 0:
                    db.supabase.table("search_configs").insert({"keyword": keyword, "target_profit": 3000}).execute()
                    print(f"  -> 追加: {keyword}")
                    added_count += 1
                else:
                    print("  -> 既登録")
            except Exception as e:
                print(f"  -> DBエラー: {e}")
            time.sleep(0.5)

        print(f"完了。新規追加: {added_count}件")

    except Exception as e:
        print(f"AI分析エラー: {e}")

if __name__ == "__main__":
    fetch_and_add_trends()