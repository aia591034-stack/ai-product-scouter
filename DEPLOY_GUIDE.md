# AI Product Scouter - デプロイガイド

このアプリを公開環境（Streamlit Cloud など）で動かすための手順です。

## 1. 必要な環境変数
公開設定の「Secrets」または「Environment Variables」に以下を設定してください。

- `GEMINI_API_KEY`: Google AI Studioから取得
- `SUPABASE_URL`: SupabaseプロジェクトのURL
- `SUPABASE_KEY`: Supabaseのanon/publicキー
- `DISCORD_WEBHOOK_URL`: (任意) 通知を送りたいDiscordのWebhook URL
- `IS_CLOUD`: `true` に設定すると、ボットの直接制御を制限し、クラウド向けのUIになります。

## 2. クラウドでのボット実行について
Streamlit Cloudは長時間実行されるプロセスを維持できないため、ボット（`bot_runner.py`）は別途 **GitHub Actions** や **Heroku**, **Render** 等のバックグラウンドジョブが動く環境で実行することをお勧めします。

### GitHub Actions で定期実行する例 (`.github/workflows/scout.yml`)
```yaml
name: AI Scouter Cron
on:
  schedule:
    - cron: '*/30 * * * *' # 30分おきに実行
jobs:
  scout:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      - name: Run Scouter & Analyzer
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: |
          python main_scouter.py
          python ai_analyzer.py
```

## 3. ファイル構成
- `packages.txt`: クラウド環境でのブラウザ実行に必要です。
- `notifier.py`: Discord通知ロジック。
- `app.py`: フィルタリング・統計機能付きの最新版。
