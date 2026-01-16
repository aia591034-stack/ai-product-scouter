import streamlit as st
import pandas as pd
from database_manager import DatabaseManager
import json
import os
import signal
import subprocess
import sys

st.set_page_config(page_title="AI Product Scouter", layout="wide")

# ボットのPIDを保存するファイル
PID_FILE = "bot.pid"

def is_bot_running():
    """ボットが実行中かチェックする"""
    if not os.path.exists(PID_FILE):
        return False
    
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # Windowsでプロセスが存在するか確認
        # tasklistコマンドで確認するのが確実
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, text=True
        )
        return str(pid) in result.stdout
    except:
        return False

def start_bot():
    """ボットを起動する"""
    if is_bot_running():
        st.warning("ボットは既に起動しています。")
        return

    # 別プロセスで起動 (pythonw.exeを使うとウィンドウが出ないが、今回はpython.exeでログ出力させる)
    # 実際には bot_runner.py 側でログファイルにリダイレクトしている
    process = subprocess.Popen(
        [sys.executable, "bot_runner.py"],
        creationflags=subprocess.CREATE_NEW_CONSOLE # 新しいウィンドウを開かない設定などが可能だが、今回はシンプルに
    )
    
    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))
    
    st.success("ボットを起動しました！")
    st.rerun()

def stop_bot():
    """ボットを停止する"""
    if not os.path.exists(PID_FILE):
        return

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # Windowsでの強制終了
        subprocess.run(["taskkill", "/F", "/PID", str(pid)])
        os.remove(PID_FILE)
        st.success("ボットを停止しました。")
        st.rerun()
    except Exception as e:
        st.error(f"停止エラー: {e}")

def load_data():
    db = DatabaseManager()
    
    # 全ての分析済み商品を取得（価格が0より大きいもの限定）
    # status が profitable, analyzed, discarded のものをすべて表示
    response = db.supabase.table("products")\
        .select("*")\
        .neq("status", "new")\
        .gt("price", 0)\
        .order("scraped_at", desc=True)\
        .execute()
    
    return response.data

def main():
    st.title("🤖 AI Product Scouter")
    
    st.sidebar.header("メニュー")
    
    # クラウド環境(スマホ閲覧用)ではボット操作を隠す
    if not os.environ.get("IS_CLOUD"):
        # ボット制御パネル
        st.sidebar.subheader("🤖 自動監視ボット")
        running = is_bot_running()
        if running:
            st.sidebar.success("状態: 実行中 🟢")
            if st.sidebar.button("監視を停止"):
                stop_bot()
        else:
            st.sidebar.error("状態: 停止中 🔴")
            if st.sidebar.button("監視を開始"):
                start_bot()
        
        # ログファイルのリンク（簡易的）
        with st.sidebar.expander("実行ログを見る", expanded=True):
            if st.button("ログを更新"):
                st.rerun()
                
            if os.path.exists("bot_log.txt"):
                try:
                    # ファイルを開き直して最新を読み込む
                    with open("bot_log.txt", "r", encoding="utf-8") as f:
                        # 最後の2000文字を取得
                        f.seek(0, os.SEEK_END)
                        size = f.tell()
                        read_size = min(size, 2000)
                        f.seek(size - read_size)
                        log_content = f.read()
                    st.code(log_content, language="text")
                except Exception as e:
                    st.error(f"ログ読み込みエラー: {e}")
            else:
                st.info("ログファイル(bot_log.txt)がまだありません。")

        st.sidebar.divider()
    
    menu = st.sidebar.radio("Go to", ["商品リサーチ", "監視設定"])
    
    if menu == "商品リサーチ":
        show_product_research()
    elif menu == "監視設定":
        show_settings()

def show_product_research():
    st.header("📈 AIトレンド速報")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        sort_order = st.selectbox("並び替え", ["新着順", "投資価値が高い順"])
    with col2:
        if st.button("データ更新"):
            st.rerun()
        
    products = load_data()
    
    if not products:
        st.info("現在、有望な商品はありません。")
        return

    # Python側でソート（投資価値順 S->A->B）
    if sort_order == "投資価値が高い順":
        rank_map = {'S': 3, 'A': 2, 'B': 1, 'C': 0}
        products.sort(
            key=lambda x: rank_map.get(x.get('ai_analysis', {}).get('investment_value', 'C'), 0),
            reverse=True
        )

    # グリッド表示
    cols = st.columns(3)
    
    for idx, item in enumerate(products):
        with cols[idx % 3]:
            with st.container(border=True):
                # 画像
                if item.get('image_url'):
                    st.image(item['image_url'], use_container_width=True)
                
                # タイトル
                st.subheader(item['title'])
                
                ai_data = item.get('ai_analysis')
                if ai_data:
                    trend_reason = ai_data.get('trend_reason', '分析中...')
                    heat = ai_data.get('heat_level', '-')
                    future = ai_data.get('future_prediction', '')
                    inv_val = ai_data.get('investment_value', '-')
                    
                    # トレンドスコア表示
                    col_score1, col_score2 = st.columns(2)
                    col_score1.metric("🔥 熱狂度", heat)
                    col_score2.metric("💎 投資価値", inv_val)
                    
                    st.markdown(f"**📈 なぜ話題？**\n{trend_reason}")
                    st.info(f"🔮 **未来予測:**\n{future}")
                    
                    st.caption(f"現在価格: ¥{item['price']:,}")
                
                st.link_button("商品ページへ", item['product_url'])
                
                # X投稿作成機能
                with st.expander("🐦 X(Twitter)投稿を作成"):
                    post_text = f"""【AIトレンド予報】今、話題の「{item['title'][:10]}...」を分析しました🔍

🔥 熱狂度: {ai_data.get('heat_level')}
💎 投資ランク: {ai_data.get('investment_value')}

📈 なぜ上がってる？
「{ai_data.get('trend_reason')}」

🔮 今後の予測
{ai_data.get('future_prediction')}

#AI #トレンド #メルカリ #{item['title'][:10]}
"""
                    st.text_area("投稿文をコピー", post_text, height=200)

                # ボタン類
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("🔄 再分析", key=f"re_ai_{item['id']}"):
                    db = DatabaseManager()
                    db.supabase.table("products").update({"status": "new", "ai_analysis": None}).eq("id", item['id']).execute()
                    st.toast("再分析待ちに設定しました。")
                    st.rerun()

                if col_btn2.button("🗑️ 除外", key=f"discard_{item['id']}"):
                    # ステータスを更新して非表示にする簡易実装
                    db = DatabaseManager()
                    db.supabase.table("products").update({"status": "discarded"}).eq("id", item['id']).execute()
                    st.toast("除外しました")
                    st.rerun()

def show_settings():
    st.header("⚙️ 監視設定")
    
    db = DatabaseManager()
    
    # 🔰 初心者向け：おすすめプリセット
    with st.expander("🔰 何を入れればいいかわからない方はこちら"):
        st.write("利益が出やすい「鉄板キーワード」を一括追加できます。")
        col_preset1, col_preset2 = st.columns(2)
        
        with col_preset1:
            if st.button("おすすめセット（カメラ・家電）を追加"):
                presets = [
                    {"keyword": "Canon EOS Kiss", "profit": 5000},
                    {"keyword": "Sony WH-1000XM4", "profit": 4000},
                    {"keyword": "iPad Air 4", "profit": 8000},
                    {"keyword": "Kindle Paperwhite", "profit": 2000},
                    {"keyword": "Bose QuietComfort", "profit": 3000},
                    {"keyword": "Nikon D5600", "profit": 6000}
                ]
                count = 0
                for p in presets:
                    try:
                        db.supabase.table("search_configs").insert({
                            "keyword": p['keyword'],
                            "target_profit": p['profit']
                        }).execute()
                        count += 1
                    except:
                        pass
                st.success(f"{count}件のキーワードを追加しました！")
                st.rerun()

        with col_preset2:
            if st.button("🔥 Googleトレンドから急上昇ワードを追加"):
                # サブプロセスで実行して結果を表示
                try:
                    result = subprocess.run(
                        [sys.executable, "trend_watcher.py"],
                        capture_output=True, text=True, encoding='utf-8'
                    )
                    st.toast("トレンド取得完了！")
                    st.info(f"実行結果:\n{result.stdout}")
                    st.rerun()
                except Exception as e:
                    st.error(f"実行エラー: {e}")

    configs = db.get_active_search_configs()
    
    # 新規追加フォーム
    st.subheader("手動追加")
    with st.form("add_config"):
        col1, col2 = st.columns(2)
        new_keyword = col1.text_input("監視キーワード")
        target_profit = col2.number_input("目標利益 (円)", value=3000)
        submitted = st.form_submit_button("追加")
        
        if submitted and new_keyword:
            try:
                db.supabase.table("search_configs").insert({
                    "keyword": new_keyword,
                    "target_profit": target_profit
                }).execute()
                st.success(f"「{new_keyword}」を追加しました")
                st.rerun()
            except Exception as e:
                st.error(f"エラー: {e}")

    # 現在の設定一覧
    st.subheader("現在の監視リスト")
    if configs:
        df = pd.DataFrame(configs)
        st.dataframe(
            df[['keyword', 'target_profit', 'is_active', 'created_at']],
            use_container_width=True
        )
    else:
        st.info("設定がありません。")

    st.divider()
    st.subheader("🧹 データメンテナンス")
    col_m1, col_m2 = st.columns(2)
    
    if col_m1.button("🔄 全商品を最初から分析し直す"):
        try:
            db.supabase.table("products")\
                .update({"status": "new", "ai_analysis": None})\
                .neq("id", "00000000-0000-0000-0000-000000000000")\
                .execute()
            st.success("全商品を分析待ちにリセットしました。ボットが順次処理します。")
        except Exception as e:
            st.error(f"エラー: {e}")

    if col_m2.button("🚫 全データを削除してリセット"):
        # 誤操作防止のため確認なしで即削除はせず、あえてここではメッセージだけにするか、
        # もしくは削除ロジックを実装
        st.warning("この操作はターミナルから 'reset_data.py' を実行してください（安全のため）。")

if __name__ == "__main__":
    main()
