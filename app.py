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
    
    # status が 'profitable' のものだけを取得するように修正（これで除外ボタンが効くようになる）
    response = db.supabase.table("products")\
        .select("*")\
        .eq("status", "profitable")\
        .gt("price", 0)\
        .order("scraped_at", desc=True)\
        .execute()
    
    return response.data

def main():
    st.title("🤖 AI Product Scouter")
    
    # サイドバー：管理者認証
    st.sidebar.header("🔑 認証")
    admin_password = st.sidebar.text_input("パスワードを入力して操作解除", type="password")
    is_admin = admin_password == os.environ.get("ADMIN_PASSWORD", "admin123")
    
    # 管理者のみに表示されるサイドバー項目
    if is_admin:
        st.sidebar.success("管理者モード：有効")
        st.sidebar.divider()
        st.sidebar.header("🤖 システム制御")
        
        if not os.environ.get("IS_CLOUD"):
            running = is_bot_running()
            if running:
                st.sidebar.success("状態: 実行中 🟢")
                if st.sidebar.button("監視を停止"):
                    stop_bot()
            else:
                st.sidebar.error("状態: 停止中 🔴")
                if st.sidebar.button("監視を開始"):
                    start_bot()
            
            with st.sidebar.expander("実行ログ"):
                if os.path.exists("bot_log.txt"):
                    with open("bot_log.txt", "r", encoding="utf-8") as f:
                        st.code(f.read()[-500:], language="text")
        else:
            st.sidebar.info("クラウド実行モード")
    else:
        st.sidebar.info("閲覧モード（制限中）")

    # メインコンテンツ
    if is_admin:
        # 管理者の場合はタブを表示
        tab1, tab2 = st.tabs(["🔍 商品リサーチ", "⚙️ 監視設定"])
        with tab1:
            show_product_research(is_admin)
        with tab2:
            show_settings(is_admin)
    else:
        # 一般ユーザーには商品リサーチのみ表示
        show_product_research(is_admin)

def show_product_research(is_admin=False):
    st.header("🔎 AIトレンド分析結果")
    
    products = load_data()
    # ... (既存のフィルタリングコード)
    # ここでは既存のフィルタリングとソート処理を維持するため、関数の最初の方を読み込みます
    if not products:
        st.info("現在、有望な商品はありません。")
        return

    # フィルタリング
    with st.expander("🔍 フィルター設定", expanded=True):
        c1, c2, c3 = st.columns(3)
        rank_filter = c1.multiselect("投資価値ランク", ["S", "A", "B"], default=["S", "A", "B"])
        min_price = c2.number_input("最低価格", value=0)
        sort_order = c3.selectbox("並び替え", ["新着順", "投資価値が高い順"])

    # フィルタリング適用
    filtered_products = [
        p for p in products 
        if p.get('ai_analysis', {}).get('investment_value') in rank_filter
        and p.get('price', 0) >= min_price
    ]

    # ソート
    if sort_order == "投資価値が高い順":
        rank_map = {'S': 3, 'A': 2, 'B': 1, 'C': 0}
        filtered_products.sort(
            key=lambda x: rank_map.get(x.get('ai_analysis', {}).get('investment_value', 'C'), 0),
            reverse=True
        )

    st.write(f"該当件数: {len(filtered_products)}件")

    # CSVダウンロード機能
    if filtered_products:
        csv_data = []
        for p in filtered_products:
            ai = p.get('ai_analysis', {})
            csv_data.append({
                "タイトル": p['title'],
                "価格": p['price'],
                "ランク": ai.get('investment_value'),
                "理由": ai.get('trend_reason'),
                "URL": p['product_url']
            })
        csv_df = pd.DataFrame(csv_data)
        st.download_button(
            label="📥 検索結果をCSVでダウンロード",
            data=csv_df.to_csv(index=False).encode('utf-8-sig'),
            file_name='profitable_products.csv',
            mime='text/csv',
        )

    # グリッド表示
    cols = st.columns(3)
    for idx, item in enumerate(filtered_products):
        with cols[idx % 3]:
            with st.container(border=True):
                # ランクに応じたバッジ
                ai_data = item.get('ai_analysis', {})
                rank = ai_data.get('investment_value', 'C')
                rank_colors = {"S": "🔴", "A": "🟠", "B": "🟢", "C": "⚪"}
                
                st.markdown(f"### {rank_colors.get(rank, '')} ランク {rank}")
                
                if item.get('image_url'):
                    st.image(item['image_url'], use_container_width=True)
                
                st.subheader(item['title'])
                st.write(f"**価格: ¥{item['price']:,}**")
                
                with st.expander("AI分析詳細"):
                    st.markdown(f"**📈 なぜ話題？**\n{ai_data.get('trend_reason')}")
                    st.info(f"🔮 **未来予測:**\n{ai_data.get('future_prediction')}")
                
                st.link_button("メルカリで見る", item['product_url'])
                
                # 管理者のみボタンを表示
                if is_admin:
                    c_btn1, c_btn2 = st.columns(2)
                    if c_btn1.button("🔄 再分析", key=f"re_{item['id']}"):
                        db = DatabaseManager()
                        db.supabase.table("products").update({"status": "new", "ai_analysis": None}).eq("id", item['id']).execute()
                        st.success("再分析待ちに設定しました")
                        st.rerun()
                    if c_btn2.button("🗑️ 除外", key=f"del_{item['id']}"):
                        db = DatabaseManager()
                        # statusをdiscardedに更新（load_dataはprofitableのみ取得するため、これで画面から消える）
                        db.supabase.table("products").update({"status": "discarded"}).eq("id", item['id']).execute()
                        st.toast("商品を除外しました")
                        st.rerun()

def show_settings(is_admin=False):
    st.header("⚙️ 監視設定")
    
    if not is_admin:
        st.warning("監視設定の変更には管理者パスワードが必要です。")
        # 設定の表示だけは許可する
        db = DatabaseManager()
        configs = db.get_active_search_configs()
        if configs:
            st.subheader("現在の監視リスト")
            df = pd.DataFrame(configs)
            st.dataframe(df[['keyword', 'target_profit', 'created_at']], use_container_width=True)
        return

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
