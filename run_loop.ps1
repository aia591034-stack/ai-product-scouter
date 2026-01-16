# AI Product Scouter 自動実行スクリプト
# 停止するには Ctrl+C を押してください

$pythonPath = ".\venv\Scripts\python.exe"
$intervalSeconds = 300  # 5分ごとに実行 (300秒)

Write-Host "🤖 AI Product Scouter 自動監視を開始します..." -ForegroundColor Cyan
Write-Host "間隔: $intervalSeconds 秒" -ForegroundColor Gray

while ($true) {
    $timestamp = Get-Date -Format "yyyy/MM/dd HH:mm:ss"
    Write-Host "`n[$timestamp] サイクル開始" -ForegroundColor Green

    # 1. スクレイピング実行
    Write-Host "1. 商品を収集しています..." -ForegroundColor Yellow
    & $pythonPath main_scouter.py
    
    # 2. AI分析実行
    Write-Host "2. AI分析を実行しています..." -ForegroundColor Yellow
    & $pythonPath ai_analyzer.py

    Write-Host "完了。次のサイクルまで待機中... ($intervalSeconds 秒)" -ForegroundColor Gray
    
    # 待機 (プログレスバー表示なしで単純スリープ)
    Start-Sleep -Seconds $intervalSeconds
}
