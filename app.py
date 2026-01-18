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
    
    /* ヘッダーデザイン */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(118, 75, 162, 0.2);
    }
    
    /* ステータスバッジ */
    .rank-badge {
        padding: 6px 14px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 0.7rem;
        text-transform: uppercase;
        display: inline-block;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
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

    /* カードデザインの微調整 */
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
        border-radius: 20px !important;
        padding: 1.5rem !important;
        background-color: white !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"]:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 12px 25px rgba(0,0,0,0.1) !important;
    }

    /* サイドバー */
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

def load_data(search_query=None, selected_genres=None):
    db = DatabaseManager()
    
    try:
        # 基本クエリ：分析済みの商品（status='new'以外）を全件対象にする
        query = db.supabase.table("products").select("*").neq("status", "new").gt("price", 0)
        
        # キーワード検索がある場合（タイトル または ジャンル）
        if search_query:
            # PostgRESTのor検索フィルタ
            filter_str = f"title.ilike.*{search_query}*,ai_analysis->>genre.ilike.*{search_query}*"
            query = query.or_(filter_str)
        elif not selected_genres:
            # 検索もジャンル選択もない場合は、デフォルトでお宝商品(profitable)を表示
            query = query.eq("status", "profitable")
            
        res = query.order("scraped_at", desc=True).limit(300).execute()
        products = res.data
        
        # ジャンル絞り込みの適用（Python側で確実に行う）
        if selected_genres:
            filtered_list = []
            for p in products:
                ai = p.get('ai_analysis')
                if isinstance(ai, str): ai = json.loads(ai)
                if ai and ai.get('genre') in selected_genres:
                    filtered_list.append(p)
            return filtered_list
            
        return products
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return []

def get_all_genres():
    """現在DBにある商品からジャンル一覧を抽出"""
    try:
        db = DatabaseManager()
        # status='new'以外の商品からジャンルを取得
        res = db.supabase.table("products").select("ai_analysis").neq("status", "new").execute()
        genres = set()
        for item in res.data:
            ai = item.get('ai_analysis')
            if isinstance(ai, str): ai = json.loads(ai)
            if isinstance(ai, dict):
                g = ai.get('genre')
                if g: genres.add(g)
        return sorted(list(genres))
    except:
        return []

# --- UI コンポーネント ---

def show_about():
    st.markdown('<div class="main-header"><h1>🚀 AI Product Scouter</h1><p>AIトレンド分析官が、24時間お宝商品を見つけ続けます。</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("### 🔍 自動トレンド発掘")
            st.write("最新ニュースやSNSからAIが「次に流行るキーワード」を特定し、自動で監視リストへ追加します。")
    with col2:
        with st.container(border=True):
            st.markdown("### 🧠 AI高精度分析")
            st.write("Gemini 2.0 が商品の希少性や将来性を判定。S〜Cランクで、仕入れ判断を強力にサポートします。")
    with col3:
        with st.container(border=True):
            st.markdown("### ⚡ 爆速通知")
            st.write("お宝（S/Aランク）が見つかった瞬間、Discordへ通知。ライバルに差をつける仕入れが可能です。")

def show_product_research(is_admin):
    st.subheader("🔎 マーケットリサーチ")
    
    # DBから最新のジャンルリストを取得
    existing_genres = get_all_genres()
    
    # 検索・ジャンルフィルターエリア
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            search_query = st.text_input("キーワード検索", placeholder="車、カメラ、ポケモンなど...", key="search_bar")
        with c2:
            # 取得したジャンルから選択できるように
            selected_genres = st.multiselect("ジャンル選択", existing_genres if existing_genres else ["データ収集中"], key="genre_sel")

    products = load_data(search_query, selected_genres)

    # 詳細フィルター
    with st.expander("🕵️ 詳細条件（ランク・価格・並び替え）"):
        f1, f2, f3 = st.columns(3)
        # 検索時は全ランクをデフォルトにする
        default_ranks = ["S", "A", "B", "C"] if search_query or selected_genres else ["S", "A", "B"]
        rank_filter = f1.multiselect("ランク", ["S", "A", "B", "C"], default=default_ranks, key="rank_f")
        min_price = f2.number_input("最低価格 (¥)", value=0, key="price_f")
        sort_order = f3.selectbox("並び替え", ["新着順", "価格が高い順", "投資価値順"], key="sort_f")

    # フィルタリング
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

    st.markdown(f"**ヒット件数:** `{len(filtered)}` 件")

    if not filtered:
        st.info("条件に一致する商品は見つかりませんでした。別のキーワードやジャンルをお試しください。")
        return

    # 商品グリッド
    grid = st.columns(3)
    for i, item in enumerate(filtered):
        with grid[i % 3]:
            ai = item.get('ai_analysis')
            if isinstance(ai, str): ai = json.loads(ai)
            rank = ai.get('investment_value', 'C')
            genre = ai.get('genre', 'その他')
            
            with st.container(border=True):
                # ランク & ジャンルバッジ
                st.markdown(f'<span class="rank-badge rank-{rank.lower()}">RANK {rank}</span><span class="genre-badge">{genre}</span>', unsafe_allow_html=True)
                
                if item['image_url']:
                    st.image(item['image_url'], use_container_width=True)
                
                st.markdown(f"#### {item['title']}")
                st.markdown(f"### <span style='color: #764ba2;'>¥{item['price']:,}</span>", unsafe_allow_html=True)
                
                with st.expander("📊 分析レポートを表示"):
                    st.write(f"**📈 注目理由:** {ai.get('trend_reason', '')}")
                    st.info(f"🔮 **未来予測:** {ai.get('future_prediction', '')}")
                
                st.link_button("メルカリで詳細を見る", item['product_url'], use_container_width=True)
                
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
    
    col1, col2 = st.columns(2)
    with col1:
        with st.form("new_keyword"):
            st.subheader("監視キーワードの追加")
            k = st.text_input("キーワード名")
            p = st.number_input("目標利益 (円)", value=3000)
            if st.form_submit_button("キーワードを保存") and k:
                db.supabase.table("search_configs").insert({"keyword": k, "target_profit": p}).execute()
                st.success(f"「{k}」を追加しました")
                st.rerun()
    with col2:
        st.subheader("クイック操作")
        if st.button("🔥 最新トレンドを自動取得"):
            subprocess.run([sys.executable, "trend_watcher.py"])
            st.success("トレンド取得を開始しました（数分かかります）")
            st.rerun()

    st.divider()
    st.subheader("現在の監視キーワード一覧")
    configs = db.get_active_search_configs()
    if configs:
        st.dataframe(pd.DataFrame(configs)[['keyword', 'target_profit', 'created_at']], use_container_width=True)

def main():
    # サイドバー
    st.sidebar.title("🛠️ 管理者メニュー")
    pw = st.sidebar.text_input("管理者パスワード", type="password")
    is_admin = pw == os.environ.get("ADMIN_PASSWORD", "admin123")
    
    if is_admin:
        st.sidebar.success("管理者として認証済み")
        if not os.environ.get("IS_CLOUD"):
            st.sidebar.divider()
            if is_bot_running():
                st.sidebar.success("監視ボット: 稼働中")
                if st.sidebar.button("ボットを停止する"): stop_bot()
            else:
                st.sidebar.error("監視ボット: 停止中")
                if st.sidebar.button("ボットを起動する"): start_bot()
    
    # メインタブの構成
    tab_h, tab_r, tab_s = st.tabs(["🏠 ホーム", "🔎 リサーチ", "⚙️ 設定"])
    with tab_h: show_about()
    with tab_r: show_product_research(is_admin)
    with tab_s:
        if is_admin: show_settings(is_admin)
        else: st.warning("この設定を表示するには管理者パスワードが必要です。")

if __name__ == "__main__":
    main()
