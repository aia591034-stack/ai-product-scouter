import os
import requests
from dotenv import load_dotenv

load_dotenv()

class Notifier:
    def __init__(self):
        self.webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    def send_profitable_item(self, product, analysis):
        """利益商品を通知する"""
        if not self.webhook_url:
            return

        inv_val = analysis.get('investment_value', 'C')
        
        # SランクまたはAランクのみ通知
        if inv_val not in ['S', 'A']:
            return

        rank_emoji = {"S": "💎", "A": "🔥", "B": "✅", "C": "👀"}
        emoji = rank_emoji.get(inv_val, "✨")

        payload = {
            "embeds": [{
                "title": f"{emoji} 【ランク {inv_val}】お宝商品を発見！",
                "description": f"**{product['title']}**",
                "url": product['product_url'],
                "color": 0x00ff00 if inv_val == 'S' else 0xffff00,
                "fields": [
                    {"name": "価格", "value": f"¥{product['price']:,}", "inline": True},
                    {"name": "熱狂度", "value": analysis.get('heat_level', '-'), "inline": True},
                    {"name": "分析理由", "value": analysis.get('trend_reason', '')},
                    {"name": "未来予測", "value": analysis.get('future_prediction', '')}
                ],
                "image": {"url": product.get('image_url', '')}
            }]
        }

        try:
            requests.post(self.webhook_url, json=payload)
        except Exception as e:
            print(f"通知エラー: {e}")
