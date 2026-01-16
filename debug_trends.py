import requests
import feedparser
import sys
import io

# 文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def debug_rss():
    url = "https://trends.google.co.jp/trends/trendingsearches/daily/rss?geo=JP"
    
    print(f"URL: {url}")
    
    # 1. 普通にfeedparserで取得
    print("\n--- Method 1: Feedparser direct ---")
    f = feedparser.parse(url)
    print(f"Status: {getattr(f, 'status', 'Unknown')}")
    print(f"Entries: {len(f.entries)}")
    if hasattr(f, 'bozo') and f.bozo:
        print(f"Bozo (Error): {f.bozo_exception}")

    # 2. User-AgentをつけてRequestsで取得
    print("\n--- Method 2: Requests with User-Agent ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers)
        print(f"Status Code: {r.status_code}")
        print(f"Content (first 200 chars): {r.text[:200]}")
        
        # 取得した文字列をfeedparserに渡す
        f2 = feedparser.parse(r.content)
        print(f"Entries via requests: {len(f2.entries)}")
        
    except Exception as e:
        print(f"Requests Error: {e}")

if __name__ == "__main__":
    debug_rss()
