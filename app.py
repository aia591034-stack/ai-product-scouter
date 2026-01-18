import streamlit as st
import pandas as pd
from database_manager import DatabaseManager
import json
import os
import subprocess
import sys

# ページ設定
st.set_page_config(
    page_title="AI Product Scouter | 次世代トレンド分析",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# モダンUIのためのカスタムCSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* ヘッダーのグラデーション */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* カードのデザイン */
    .product-card {
        background: white;
        padding: 1.5rem;
        border-radius: 20px;
        border: 1px solid #f0f0f0;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
    }
    
    .product-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.1);
    }
    
    /* ランクバッジ */
    .rank-badge {
        padding: 0.4rem 1rem;
        border-radius: 50px;
        font-weight: bold;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 1rem;
    }
    
    .rank-s { background-color: #ffe3e3; color: #ff4b4b; border: 1px solid #ff4b4b; }
    .rank-a { background-color: #fff4e6; color: #fd7e14; border: 1px solid #fd7e14; }
    .rank-b { background-color: #ebfbee; color: #40c057; border: 1px solid #40c057; }
    .rank-c { background-color: #f8f9fa; color: #868e96; border: 1px solid #868e96; }
    
    /*ジャンルタグ */
    .genre-tag {
        background-color: #f1f3f5;
        color: #495057;
        padding: 0.2rem 0.6rem;
        border-radius: 5px;
        font-size: 0.75rem;
        margin-left: 0.5rem;
    }

    /*サイドバーの調整 */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    
    /*タブのスタイル */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-weight: 600;
        font-size: 1rem;
        color: #495057;
    }

    .stTabs [aria-selected="true"] {
        color: #764ba2 !important;
        border-bottom-color: #764ba2 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ロジック部分 ---

PID_FILE = "bot.pid"

def is_bot_running():
    if not os.path.exists(PID_FILE): return False
    try:
        with open(PID_FILE, "r") as f: pid = int(f.read().strip())
        result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
        return str(pid) in result.stdout
    except: return False

def start_bot():
    if is_bot_running(): return
    process = subprocess.Popen([sys.executable, "bot_runner.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    with open(PID_FILE, "w") as f: f.write(str(process.pid))
    st.rerun()

def stop_bot():
    if not os.path.exists(PID_FILE): return
    try:
        with open(PID_FILE, "r") as f: pid = int(f.read().strip())
        subprocess.run(["taskkill", "/F", "/PID", str(pid)])
        os.remove(PID_FILE)
        st.rerun()
    except: pass

def load_data(search_query=None, selected_genres=None):
    db = DatabaseManager()
    query = db.supabase.table("products").select("*").gt("price", 0)
    
    if search_query:
        # キーワード検索: タイトルまたはジャンル(ai_analysis->>genre)
        res = query.or_(f"title.ilike.%{search_query}%",f"ai_analysis->>genre.ilike.%{search_query}%")\
            .neq("status", "new")\
            .order("scraped_at", desc=True)\
            .limit(200).execute()
        products = res.data
    else:
        # 通常時はお宝のみ
        res = query.eq("status", "profitable").order("scraped_at", desc=True).execute()
        products = res.data
    
    # ジャンル絞り込みの適用
    if selected_genres:
        products = [p for p in products if p.get('ai_analysis', {}).get('genre') in selected_genres]
        
    return products

def get_all_genres():
    db = DatabaseManager()
    res = db.supabase.table("products").select("ai_analysis").neq("status", "new").execute()
    genres = set()
    for item in res.data:
        if isinstance(item.get('ai_analysis'), dict):
            g = item['ai_analysis'].get('genre')
            if g: genres.add(g)
    return sorted(list(genres))

# --- UI コンポーネント ---

def show_about():
    st.markdown('<div class="main-header"><h1>🚀 AI Product Scouter</h1><p>AIが24時間、世界中のトレンドからお宝商品を発見し続けます。</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🔍 探す")
        st.write("AIが最新ニュースから「次に流行るキーワード」を自動で特定し、監視リストに追加します。")
    with col2:
        st.markdown("### 🤖 分析する")
        st.write("Gemini 2.0 が商品を1つずつ鑑定し、背景・将来性・投資価値をランク付けします。")
    with col3:
        st.markdown("### 💰 稼ぐ")
        st.write("お宝（S/Aランク）が見つかったら、即座にDiscordへ通知。チャンスを逃しません。")

    st.divider()
    with st.expander("⚖️ 免責事項を確認する"):
        st.warning("本ツールはAIの予測に基づく情報提供のみを目的としています。最終的な判断は自己責任で行ってください。")

def show_product_research(is_admin):
    st.subheader("🔎 トレンドリサーチ")
    
    all_genres = get_all_genres()
    
    # 検索エリアをカード風に
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            search_query = st.text_input("キーワード検索", placeholder="商品名やジャンルを入力...", key="search_bar")
        with c2:
            selected_genres = st.multiselect("ジャンルで絞り込む", all_genres, key="genre_sel")

    products = load_data(search_query, selected_genres)

    # フィルター設定
    with st.expander("🕵️ 詳細フィルター"):
        f1, f2, f3 = st.columns(3)
        available_ranks = ["S", "A", "B", "C"]
        rank_filter = f1.multiselect("ランク", available_ranks, default=["S", "A", "B"], key="rank_f")
        min_price = f2.number_input("最低価格 (¥)", value=0, key="price_f")
        sort_order = f3.selectbox("並び替え", ["新着順", "価格が高い順", "投資価値順"], key="sort_f")

    # フィルタリング適用
    filtered = [p for p in products if p.get('ai_analysis', {}).get('investment_value') in rank_filter and p['price'] >= min_price]
    
    # ソート
    if sort_order == "投資価値順":
        rm = {'S':3, 'A':2, 'B':1, 'C':0}
        filtered.sort(key=lambda x: rm.get(x.get('ai_analysis', {}).get('investment_value', 'C'), 0), reverse=True)
    elif sort_order == "価格が高い順":
        filtered.sort(key=lambda x: x['price'], reverse=True)

    st.caption(f"該当商品: {len(filtered)} 件")

    # グリッド表示
    grid_cols = st.columns(3)
    for i, item in enumerate(filtered):
        with grid_cols[i % 3]:
            ai = item.get('ai_analysis', {})
            rank = ai.get('investment_value', 'C')
            genre = ai.get('genre', 'その他')
            
            # カード型HTML
            st.markdown(f"""
                <div class="product-card">
                    <span class="rank-badge rank-{rank.lower()}">RANK {rank}</span>
                    <span class="genre-tag">{genre}</span>
                    <h4 style="margin-top: 0.5rem; height: 3em; overflow: hidden;">{item['title']}</h4>
                    <p style="font-size: 1.2rem; font-weight: bold; color: #764ba2;">¥{item['price']:,}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # 画像と詳細
            if item['image_url']: st.image(item['image_url'], use_container_width=True)
            
            with st.expander("📊 AI鑑定レポート"):
                st.write(f"**📈 理由:** {ai.get('trend_reason')}")
                st.info(f"🔮 **予測:** {ai.get('future_prediction')}")
            
            st.link_button("メルカリで見る", item['product_url'], use_container_width=True)
            
            if is_admin:
                a1, a2 = st.columns(2)
                if a1.button("🔄 再分析", key=f"re_{item['id']}"):
                    DatabaseManager().supabase.table("products").update({"status": "new", "ai_analysis": None}).eq("id", item['id']).execute()
                    st.rerun()
                if a2.button("🗑️ 除外", key=f"del_{item['id']}"):
                    DatabaseManager().supabase.table("products").update({"status": "discarded"}).eq("id", item['id']).execute()
                    st.rerun()
            st.write("---")

def show_settings(is_admin):
    if not is_admin: return
    st.subheader("⚙️ 管理設定")
    db = DatabaseManager()
    
    col1, col2 = st.columns(2)
    with col1:
        with st.form("add"):
            k = st.text_input("新しい監視キーワード")
            p = st.number_input("目標利益", value=3000)
            if st.form_submit_button("追加") and k:
                db.supabase.table("search_configs").insert({"keyword": k, "target_profit": p}).execute()
                st.rerun()
    with col2:
        st.write("おすすめ機能")
        if st.button("🔥 トレンドから自動追加"):
            subprocess.run([sys.executable, "trend_watcher.py"])
            st.rerun()

    st.write("現在の監視リスト")
    configs = db.get_active_search_configs()
    if configs: st.dataframe(pd.DataFrame(configs)[['keyword', 'target_profit', 'created_at']], use_container_width=True)

# --- メイン実行 ---

def main():
    # サイドバー
    st.sidebar.title("🔐 Admin Area")
    pw = st.sidebar.text_input("Passphrase", type="password")
    is_admin = pw == os.environ.get("ADMIN_PASSWORD", "admin123")
    
    if is_admin:
        st.sidebar.success("Welcome, Admin")
        if not os.environ.get("IS_CLOUD"):
            st.sidebar.divider()
            if is_bot_running():
                st.sidebar.success("Bot: Running")
                if st.sidebar.button("Stop Bot"): stop_bot()
            else:
                st.sidebar.error("Bot: Offline")
                if st.sidebar.button("Start Bot"): start_bot()
    
    # メインタブ
    if is_admin:
        t1, t2, t3 = st.tabs(["🏠 Home", "🔎 Research", "⚙️ Settings"])
        with t1: show_about()
        with t2: show_product_research(is_admin)
        with t3: show_settings(is_admin)
    else:
        t1, t2 = st.tabs(["🏠 Home", "🔎 Research"])
        with t1: show_about()
        with t2: show_product_research(is_admin)

if __name__ == "__main__":
    main()