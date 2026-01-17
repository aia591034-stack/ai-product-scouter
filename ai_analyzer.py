import os
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv
from database_manager import DatabaseManager
from notifier import Notifier
import sys
import io

# 文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

# Gemini設定
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

genai.configure(api_key=API_KEY)
# Use gemini-2.0-flash as confirmed by list_models
model = genai.GenerativeModel('gemini-2.0-flash')

def analyze_product_with_ai(product):
    """Geminiを使って商品を分析する"""
    
    prompt = f"""
    あなたはプロの「トレンド分析官」です。
    Googleトレンドで急上昇し、メルカリでも活発に取引されている以下の商品について、
    「なぜ今、価格が上がっているのか？」という背景と、今後の予測を行ってください。
    
    【商品情報】
    タイトル: {product['title']}
    現在価格: ¥{product['price']}
    
    【分析要件】
    1. trend_reason: 価格上昇や注目の理由を推測（例：「本日発売の限定品」「YouTuber〇〇が紹介」「生産終了のニュース」など）。推測できない場合は商品特徴から分析。
    2. heat_level: 熱狂度を "High"(争奪戦), "Medium"(人気), "Low"(通常) で判定。
    3. future_prediction: 今後の価格推移予測（例：「再販がないためさらに高騰する」「ブームが一過性のため下落する」）。
    4. investment_value: 投資価値があるか（S/A/B/C判定）。
    
    【出力フォーマット(JSONのみ)】
    {{
      "trend_reason": "本日公開の映画『〇〇』の入場者特典であり、非売品のため需要が急増している。",
      "heat_level": "High",
      "future_prediction": "配布終了後さらに高騰する可能性があるが、フリマ出品数も多いため一瞬の下落に注意。",
      "investment_value": "A"
    }}
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        result_json = json.loads(response.text)
        return result_json
    except Exception as e:
        print(f"AI Analysis Error for {product['title']}: {e}")
        return None

def run_analysis_loop():
    db = DatabaseManager()
    notifier = Notifier()
    
    print("AI分析プロセスを開始します...")
    
    # 処理件数を5件から30件に増やして、バックログ（溜まり）を防ぐ
    new_products = db.get_new_products(limit=30)
    
    if not new_products:
        print("分析待ちの商品はありません。")
        return

    for product in new_products:
        print(f"\nAnalyzing: {product['title']} (¥{product['price']})")
        
        analysis = analyze_product_with_ai(product)
        
        if analysis:
            print(f"Result: {json.dumps(analysis, ensure_ascii=False)}")
            
            # ステータスの決定
            inv_val = analysis.get('investment_value', 'C')
            if inv_val in ['S', 'A', 'B']: # Bランクも表示対象に含める
                new_status = 'profitable' 
            else:
                new_status = 'discarded'
            
            # DB更新
            db.update_product_analysis(product['id'], analysis, new_status)
            
            # 通知（利益商品の場合）
            if new_status == 'profitable':
                notifier.send_profitable_item(product, analysis)
            
            # API制限考慮
            time.sleep(2)
        else:
            print("Skipping update due to error.")

if __name__ == "__main__":
    run_analysis_loop()
