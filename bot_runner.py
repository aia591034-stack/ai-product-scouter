import time
import subprocess
import sys
import os

# 実行するスクリプトのパス
PYTHON_EXE = sys.executable
SCOUTER_SCRIPT = "main_scouter.py"
ANALYZER_SCRIPT = "ai_analyzer.py"
TREND_SCRIPT = "trend_watcher.py"

def run_bot_loop():
    print(f"Bot runner started. PID: {os.getpid()}")
    
    while True:
        try:
            print("\n--- Starting Cycle ---")
            
            # 0. トレンド取得 (毎回やると多いので、本当は1日1回が良いがデモ用に毎回)
            print("Checking Trends...")
            subprocess.run([PYTHON_EXE, TREND_SCRIPT], check=False)

            # 1. Scraper実行
            print("Running Scraper...")
            subprocess.run([PYTHON_EXE, SCOUTER_SCRIPT], check=False)
            
            # 2. Analyzer実行
            print("Running Analyzer...")
            subprocess.run([PYTHON_EXE, ANALYZER_SCRIPT], check=False)
            
            print("Cycle finished. Waiting 300 seconds...")
            time.sleep(300) # 5分待機
            
        except KeyboardInterrupt:
            print("Bot stopped by user.")
            break
        except Exception as e:
            print(f"Error in bot loop: {e}")
            time.sleep(60) # エラー時は1分待機してリトライ

if __name__ == "__main__":
    # 出力をファイルにリダイレクト（ログ保存のため）
    # flush=Trueにするためにラッパークラスを作成
    class Unbuffered(object):
       def __init__(self, stream):
           self.stream = stream
       def write(self, data):
           self.stream.write(data)
           self.stream.flush()
       def writelines(self, datas):
           self.stream.writelines(datas)
           self.stream.flush()
       def __getattr__(self, attr):
           return getattr(self.stream, attr)

    with open("bot_log.txt", "a", encoding="utf-8") as f:
        sys.stdout = Unbuffered(f)
        sys.stderr = Unbuffered(f)
        run_bot_loop()
