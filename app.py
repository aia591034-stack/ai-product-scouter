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
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(118, 75, 162, 0.2);
    }
    
    .rank-badge {
        padding: 6px 14px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 0.7rem;
        text-transform: uppercase;
        display: inline-block;
    }
    
    .rank-s { background-color: #ff4b4b; color: white; }
    .rank-a { background-color: #fd7e14; color: white; }
    .rank-b { background-color: #40c057; color: white; }
    .rank-c { background-color: #868e96; color: white; }
    
    .genre-badge {
        background-color: #e9ecef;
        color: #495057;
        padding: 6px 14px;
        border-radius: 50px;
        font-size: 0.7rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 5px;
        border: 1px solid #dee2e6;
    }

    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
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

@st.cache_data(ttl=60) # 1分間キャッシュ
def get_all_genres():
    """DBから動的にジャンルを取得する（高速化と安定化のためキャッシュ使用）"""
    try:
        db = DatabaseManager()
        # 最新の1000件からジャンルを抽出（全件だと重いため）
        res = db.supabase.table("products").select("ai_analysis").neq("status", "new").order("scraped_at", desc=True).limit(1000).execute()
        genres = set()
        for item in res.data:
            ai = item.get('ai_analysis')
            if not ai: continue
            if isinstance(ai, str):
                try: ai = json.loads(ai)
                except: continue
            if isinstance(ai, dict):
                g = ai.get('genre')
                if g: genres.add(g)
        
        return sorted(list(genres))
    except Exception as e:
        print(f"Genre fetch error: {e}")
        return []

def load_data(search_query=None, selected_genres=None):
    db = DatabaseManager()
    try:
        query = db.supabase.table("products").select("*").neq("status", "new").gt("price", 0)
        
        if search_query:
            # * を使ったワイルドカード検索
            filter_str = f"title.ilike.*{search_query}*,ai_analysis->>genre.ilike.*{search_query}*"
            query = query.or_(filter_str)
        elif not selected_genres:
            # デフォルト表示
            query = query.eq("status", "profitable")
            
        res = query.order("scraped_at", desc=True).limit(300).execute()
        products = res.data
        
        # Python側での厳密なジャンルフィルタリング
        if selected_genres:
            filtered = []
            for p in products:
                ai = p.get('ai_analysis')
                if isinstance(ai, str): ai = json.loads(ai)
                if ai and ai.get('genre') in selected_genres:
                    filtered.append(p)
            return filtered
            
        return products
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return []

# --- UI ---

def show_about():
    st.markdown('<div class="main-header"><h1>🚀 AI Product Scouter</h1><p>AIが24時間、世界中のお宝商品を見つけ続けます。</p></div>', unsafe_allow_html=True)
    st.info("💡 **ヒント:** ジャンルが表示されない場合は、新しい商品を収集するか、既存の商品を「再分析」してください。")

def show_product_research(is_admin):
    st.subheader("🔎 マーケットリサーチ")
    
    # ジャンル一覧の取得
    genres = get_all_genres()
    
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            search_query = st.text_input("キーワード検索", placeholder="商品名やジャンルを入力（例: 車）", key="search_bar")
        with c2:
            # 取得したジャンルを表示（空の場合はメッセージを出す）
            if genres:
                selected_genres = st.multiselect("🏷️ ジャンルで絞り込む", genres, key="genre_sel")
            else:
                st.warning("ジャンルデータがまだありません")
                selected_genres = None

    products = load_data(search_query, selected_genres)

    with st.expander("🕵️ 詳細フィルターと並び替え"):
        f1, f2, f3 = st.columns(3)
        rank_filter = f1.multiselect("ランク", ["S", "A", "B", "C"], default=["S", "A", "B"], key="rank_f")
        min_price = f2.number_input("最低価格 (¥)", value=0, key="price_f")
        sort_order = f3.selectbox("並び替え", ["新着順", "価格が高い順", "投資価値順"], key="sort_f")
        
        if st.button("🔄 ジャンル一覧を更新"):
            st.cache_data.clear()
            st.rerun()

    # フィルタリング適用
    filtered = []
    for p in products:
        ai = p.get('ai_analysis')
        if isinstance(ai, str): ai = json.loads(ai)
        rank = ai.get('investment_value', 'C') if ai else 'C'
        if rank in rank_filter and p['price'] >= min_price:
            filtered.append(p)
    
    # ソート
    if sort_order == "投資価値順":
        rm = {'S':3, 'A':2, 'B':1, 'C':0}
        filtered.sort(key=lambda x: rm.get((json.loads(x['ai_analysis']) if isinstance(x['ai_analysis'], str) else x['ai_analysis']).get('investment_value', 'C'), 0), reverse=True)
    elif sort_order == "価格が高い順":
        filtered.sort(key=lambda x: x['price'], reverse=True)

    st.markdown(f"**表示件数:** `{len(filtered)}` 件")

    if not filtered:
        st.info("条件に一致する商品は見つかりませんでした。")
        return

    grid = st.columns(3)
    for i, item in enumerate(filtered):
        with grid[i % 3]:
            ai = item.get('ai_analysis')
            if isinstance(ai, str): ai = json.loads(ai)
            rank = ai.get('investment_value', 'C')
            genre = ai.get('genre', 'その他')
            
            with st.container(border=True):
                st.markdown(f'<span class="rank-badge rank-{rank.lower()}">RANK {rank}</span><span class="genre-badge">{genre}</span>', unsafe_allow_html=True)
                if item['image_url']: st.image(item['image_url'], use_container_width=True)
                st.markdown(f"#### {item['title']}")
                st.markdown(f"### <span style='color: #764ba2;'>¥{item['price']:,}</span>", unsafe_allow_html=True)
                
                with st.expander("📊 AI鑑定レポート"):
                    st.write(f"**📈 理由:** {ai.get('trend_reason', '')}")
                    st.info(f"🔮 **予測:** {ai.get('future_prediction', '')}")
                
                st.link_button("メルカリで見る", item['product_url'], use_container_width=True)
                
                if is_admin:
                    a1, a2 = st.columns(2)
                    if a1.button("🔄 再分析", key=f"re_{item['id']}"):
                        DatabaseManager().supabase.table("products").update({"status": "new", "ai_analysis": None}).eq("id", item['id']).execute()
                        st.rerun()
                    if a2.button("🗑️ 除外", key=f"del_{item['id']}"):
                        DatabaseManager().supabase.table("products").update({"status": "discarded"}).eq("id", item['id']).execute()
                        st.rerun()

def show_settings(is_admin):
    if not is_admin: return
    st.header("⚙️ システム設定")
    db = DatabaseManager()
    
    c1, c2 = st.columns(2)
    with c1:
        with st.form("new_k"):
            k = st.text_input("キーワード")
            p = st.number_input("目標利益", value=3000)
            if st.form_submit_button("保存") and k:
                db.supabase.table("search_configs").insert({"keyword": k, "target_profit": p}).execute()
                st.rerun()
    with c2:
        if st.button("🔥 トレンドから自動追加"):
            subprocess.run([sys.executable, "trend_watcher.py"])
            st.rerun()

    configs = db.get_active_search_configs()
    if configs:
        st.dataframe(pd.DataFrame(configs)[['keyword', 'target_profit', 'created_at']], use_container_width=True)

def main():
    st.sidebar.title("🛠️ Admin Area")
    pw = st.sidebar.text_input("Password", type="password")
    is_admin = pw == os.environ.get("ADMIN_PASSWORD", "admin123")
    
    if is_admin:
        st.sidebar.success("Welcome, Admin")
        if not os.environ.get("IS_CLOUD"):
            if is_bot_running():
                st.sidebar.success("Bot: Running")
                if st.sidebar.button("Stop"): stop_bot()
            else:
                st.sidebar.error("Bot: Offline")
                if st.sidebar.button("Start"): start_bot()
    
    tab_h, tab_r, tab_s = st.tabs(["🏠 ホーム", "🔎 リサーチ", "⚙️ 設定"])
    with tab_h: show_about()
    with tab_r: show_product_research(is_admin)
    with tab_s:
        if is_admin: show_settings(is_admin)
        else: st.warning("管理者パスワードを入力してください。")

if __name__ == "__main__":
    main()