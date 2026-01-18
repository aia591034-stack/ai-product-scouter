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

    process = subprocess.Popen(
        [sys.executable, "bot_runner.py"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
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
        
        subprocess.run(["taskkill", "/F", "/PID", str(pid)])
        os.remove(PID_FILE)
        st.success("ボットを停止しました。")
        st.rerun()
    except Exception as e:
        st.error(f"停止エラー: {e}")

def load_data(search_query=None, selected_genres=None):
    db = DatabaseManager()
    
    query = db.supabase.table("products").select("*").gt("price", 0)
    
    if search_query:
        # タイトル検索
        response = query.ilike("title", f"%{search_query}%")\
            .neq("status", "new")\
            .order("scraped_at", desc=True)\
            .limit(200)\
            .execute()
        products = response.data
        
        # タイトルにヒットしなかった場合、またはジャンルでも検索したい場合
        # ジャンル（ai_analysis->>genre）での検索を追加
        genre_res = db.supabase.table("products").select("*")\
            .neq("status", "new")\
            .filter("ai_analysis->>genre", "ilike", f"%{search_query}%")\
            .limit(100).execute()
            
        # 統合（重複排除）
        existing_ids = {p['id'] for p in products}
        for p in genre_res.data:
            if p['id'] not in existing_ids:
                products.append(p)
    else:
        # 通常時は 'profitable' のみ表示
        response = query.eq("status", "profitable")\
            .order("scraped_at", desc=True)\
            .execute()
        products = response.data
    
    # ジャンルフィルターの適用（Python側）
    if selected_genres:
        products = [p for p in products if p.get('ai_analysis', {}).get('genre') in selected_genres]
        
    return products

def get_all_genres():
    """DB内の全ジャンルを取得"""
    db = DatabaseManager()
    res = db.supabase.table("products").select("ai_analysis").neq("status", "new").execute()
    genres = set()
    for item in res.data:
        g = item.get('ai_analysis', {}).get('genre')
        if g:
            genres.add(g)
    return sorted(list(genres))

def main():
    st.title("🤖 AI Product Scouter")
    
    # サイドバー：管理者認証
    st.sidebar.header("🔑 認証")
    admin_password = st.sidebar.text_input("パスワードを入力して操作解除", type="password")
    is_admin = admin_password == os.environ.get("ADMIN_PASSWORD", "admin123")
    
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
        tab_about, tab_research, tab_settings = st.tabs(["📖 使い方・免責事項", "🔍 商品リサーチ", "⚙️ 監視設定"])
        with tab_about:
            show_about()
        with tab_research:
            show_product_research(is_admin)
        with tab_settings:
            show_settings(is_admin)
    else:
        tab_about, tab_research = st.tabs(["📖 使い方・免責事項", "🔍 商品リサーチ"])
        with tab_about:
            show_about()
        with tab_research:
            show_product_research(is_admin)

def show_about():
    st.header("📖 はじめての方へ")
    
    st.markdown("""
    ### 🤖 AI Product Scouter とは？
    このツールは、**最新のニュースやトレンドをAI（Gemini）が読み解き、将来的に価格が高騰したり、需要が急増しそうな商品を自動で見つけ出す**リサーチアシスタントです。
    """ )
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        **🔍 リサーチの仕組み**
        1. **トレンド予測**: AIが毎日のニュースからお宝キーワードを抽出。
        2. **自動巡回**: 24時間、メルカリの新着商品を自動チェック。
        3. **AI分析**: 見つけた商品を1つずつAIが精密鑑定し、価値を判定。
        """ )
    with col2:
        st.success("""
        **💎 ランクの見方**
        - **🔴 ランク S**: 極めて高い投資価値・争奪戦必至。
        - **🟠 ランク A**: 有望なトレンド商品。早めのチェックを推奨。
        - **🟢 ランク B**: 安定した需要あり。利益の可能性あり。
        - **⚪ ランク C**: 通常の流通品、または市場価格並み。
        """ )

    st.divider() 
    
    st.header("⚖️ 免責事項")
    st.warning("""
    当サイト（AI Product Scouter）のご利用にあたっては、以下の事項を必ずご確認ください。
    
    1. **情報の正確性について**
       本ツールが提供する分析結果や未来予測は、AIによる推測に基づいたものであり、その正確性、完全性、将来の利益を保証するものではありません。
    2. **投資・購入判断について**
       商品の購入や転売等の最終的な判断は、必ずユーザーご自身の責任で行ってください。
    """ )

def show_product_research(is_admin=False):
    st.header("🔎 商品リサーチ")
    
    all_genres = get_all_genres()
    
    col_search, col_genre = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 キーワード・ジャンルで探す", placeholder="例: 車, 家電, ポケモン...", key="research_search_input")
    with col_genre:
        selected_genres = st.multiselect("🏷️ ジャンル絞り込み", all_genres, key="genre_filter")
    
    products = load_data(search_query, selected_genres)
    
    if not products:
        if search_query:
            st.info(f"「{search_query}」に一致する商品は見つかりませんでした。")
        else:
            st.info("現在、有望な商品はありません。")
        return

    with st.expander("🕵️ 詳細フィルター", expanded=False):
        c1, c2, c3 = st.columns(3)
        available_ranks = ["S", "A", "B", "C"] if search_query else ["S", "A", "B"]
        rank_filter = c1.multiselect("投資価値ランク", available_ranks, default=available_ranks, key="filter_rank_select")
        min_price = c2.number_input("最低価格", value=0, key="filter_min_price")
        sort_order = c3.selectbox("並び替え", ["新着順", "価格が高い順", "投資価値が高い順"], key="filter_sort_order")

    filtered_products = [
        p for p in products 
        if p.get('ai_analysis', {}).get('investment_value') in rank_filter
        and p.get('price', 0) >= min_price
    ]
    
    if sort_order == "投資価値が高い順":
        rank_map = {'S': 3, 'A': 2, 'B': 1, 'C': 0}
        filtered_products.sort(key=lambda x: rank_map.get(x.get('ai_analysis', {}).get('investment_value', 'C'), 0), reverse=True)
    elif sort_order == "価格が高い順":
        filtered_products.sort(key=lambda x: x.get('price', 0), reverse=True)

    st.write(f"表示件数: {len(filtered_products)}件")

    if filtered_products:
        csv_data = [{"タイトル": p['title'], "価格": p['price'], "ランク": p.get('ai_analysis', {}).get('investment_value'), "ジャンル": p.get('ai_analysis', {}).get('genre'), "URL": p['product_url']} for p in filtered_products]
        st.download_button("📥 CSVダウンロード", pd.DataFrame(csv_data).to_csv(index=False).encode('utf-8-sig'), "scout_results.csv", "text/csv", key="download_csv_btn")

    cols = st.columns(3)
    for idx, item in enumerate(filtered_products):
        with cols[idx % 3]:
            with st.container(border=True):
                ai_data = item.get('ai_analysis', {})
                rank = ai_data.get('investment_value', 'C')
                genre = ai_data.get('genre', 'その他')
                rank_colors = {"S": "🔴", "A": "🟠", "B": "🟢", "C": "⚪"}
                
                col_r, col_g = st.columns(2)
                col_r.markdown(f"### {rank_colors.get(rank, '')} ランク {rank}")
                col_g.markdown(f"**🏷️ {genre}**")
                
                if item.get('image_url'):
                    st.image(item['image_url'], use_container_width=True)
                
                st.subheader(item['title'])
                st.write(f"**価格: ¥{item['price']:,}**")
                
                with st.expander("AI分析詳細"):
                    st.markdown(f"**📈 理由:** {ai_data.get('trend_reason')}")
                    st.info(f"🔮 **予測:** {ai_data.get('future_prediction')}")
                
                st.link_button("メルカリで見る", item['product_url'])
                
                if is_admin:
                    c_btn1, c_btn2 = st.columns(2)
                    if c_btn1.button("🔄 再分析", key=f"re_{item['id']}"):
                        DatabaseManager().supabase.table("products").update({"status": "new", "ai_analysis": None}).eq("id", item['id']).execute()
                        st.rerun()
                    if c_btn2.button("🗑️ 除外", key=f"del_{item['id']}"):
                        DatabaseManager().supabase.table("products").update({"status": "discarded"}).eq("id", item['id']).execute()
                        st.rerun()

def show_settings(is_admin=False):
    st.header("⚙️ 監視設定")
    if not is_admin:
        st.warning("管理者権限が必要です。")
        return

    db = DatabaseManager()
    
    with st.expander("🔰 おすすめプリセット"):
        if st.button("人気ガジェットセットを追加"):
            presets = [{"keyword": "iPad Air", "profit": 5000}, {"keyword": "Sony WH-1000XM5", "profit": 3000}]
            for p in presets:
                db.supabase.table("search_configs").insert(p).execute()
            st.success("追加しました")
            st.rerun()

        if st.button("🔥 トレンドから自動追加"):
            subprocess.run([sys.executable, "trend_watcher.py"])
            st.rerun()

    with st.form("add_keyword_form"):
        k = st.text_input("監視キーワード")
        p = st.number_input("目標利益", value=3000)
        if st.form_submit_button("追加") and k:
            db.supabase.table("search_configs").insert({"keyword": k, "target_profit": p}).execute()
            st.rerun()

    configs = db.get_active_search_configs()
    if configs:
        st.dataframe(pd.DataFrame(configs)[['keyword', 'target_profit', 'created_at']], use_container_width=True)

if __name__ == "__main__":
    main()
