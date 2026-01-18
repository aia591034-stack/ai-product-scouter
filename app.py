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
        padding: 2.5rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(118, 75, 162, 0.2);
    }
    
    /* カードのデザイン */
    .product-card-container {
        background: white;
        padding: 0;
        border-radius: 20px;
        border: 1px solid #f0f0f0;
        overflow: hidden;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        margin-bottom: 20px;
    }
    
    .product-card-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    
    /* ステータスバッジ */
    .badge-container {
        display: flex;
        gap: 8px;
        padding: 15px 15px 0 15px;
    }
    
    .rank-badge {
        padding: 4px 12px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
    }
    
    .rank-s { background-color: #ff4b4b; color: white; }
    .rank-a { background-color: #fd7e14; color: white; }
    .rank-b { background-color: #40c057; color: white; }
    .rank-c { background-color: #868e96; color: white; }
    
    .genre-badge {
        background-color: #f1f3f5;
        color: #495057;
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* フォームと入力エリア */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 1px solid #e9ecef;
    }

    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    </style>
", unsafe_allow_html=True)

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
        if search_query:
            # PostgRESTの記法に修正: * をワイルドカードに使用
            # JSONパスも正確に指定
            filter_str = f"title.ilike.*{search_query}*,ai_analysis->>genre.ilike.*{search_query}*"
            res = db.supabase.table("products").select("*")\
                .or_(filter_str)
                .neq("status", "new")\
                .gt("price", 0)
                .order("scraped_at", desc=True)
                .limit(200).execute()
        else:
            res = db.supabase.table("products").select("*")\
                .eq("status", "profitable")\
                .gt("price", 0)
                .order("scraped_at", desc=True)
                .execute()
        
        products = res.data
        
        # ジャンル絞り込み (Python側で確実に行う)
        if selected_genres:
            filtered_products = []
            for p in products:
                ai = p.get('ai_analysis')
                if isinstance(ai, str): ai = json.loads(ai)
                if ai and ai.get('genre') in selected_genres:
                    filtered_products.append(p)
            return filtered_products
            
        return products
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return []

def get_all_genres():
    try:
        db = DatabaseManager()
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
    st.markdown("<div class=\"main-header\"><h1>🤖 AI Product Scouter</h1><p>AIトレンド分析官が、あなたに代わってお宝商品を見つけ出します。</p></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("### 🛰️ トレンド追跡")
            st.write("最新ニュースやGoogleトレンドをAIが24時間解析。次に価格が上がるキーワードを自動で抽出します。")
    with c2:
        with st.container(border=True):
            st.markdown("### 🧠 精密AI鑑定")
            st.write("Gemini 2.0 が商品の希少性、需要、将来の相場を予測し、S〜Cランクで格付け。お宝を逃しません。")
    with c3:
        with st.container(border=True):
            st.markdown("### 🔔 即時通知")
            st.write("お宝（S/Aランク）を検知すると、Discordに画像を添えて即通知。スマホ1つで仕入れ判断が可能です。")

def show_product_research(is_admin):
    st.subheader("🔎 トレンドリサーチ")
    
    all_genres = get_all_genres()
    
    # 検索・フィルターエリア
    with st.container(border=True):
        col_s, col_g = st.columns([2, 1])
        with col_s:
            search_query = st.text_input("キーワード検索（商品名・ジャンル・車など）", placeholder="何を探しますか？", key="main_search")
        with col_g:
            selected_genres = st.multiselect("ジャンル絞り込み", all_genres if all_genres else ["データなし"], key="genre_filter")

    products = load_data(search_query, selected_genres)

    # 詳細フィルター
    with st.expander("🕵️ 詳細設定（ランク・価格・ソート）"):
        f1, f2, f3 = st.columns(3)
        rank_filter = f1.multiselect("ランク", ["S", "A", "B", "C"], default=["S", "A", "B"], key="rank_f")
        min_price = f2.number_input("最低価格", value=0, step=1000)
        sort_order = f3.selectbox("並び替え", ["新着順", "価格が高い順", "投資価値順"])

    # Python側フィルタリング
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
        filtered.sort(key=lambda x: rm.get((x.get('ai_analysis') if isinstance(x.get('ai_analysis'), dict) else json.loads(x.get('ai_analysis', '{}'))).get('investment_value', 'C'), 0), reverse=True)
    elif sort_order == "価格が高い順":
        filtered.sort(key=lambda x: x['price'], reverse=True)

    st.markdown(f"**表示件数:** `{len(filtered)}` 件")

    # カードグリッド
    if not filtered:
        st.info("条件に一致する商品が見つかりませんでした。別のキーワードをお試しください。")
        return

    grid = st.columns(3)
    for i, item in enumerate(filtered):
        with grid[i % 3]:
            ai = item.get('ai_analysis')
            if isinstance(ai, str): ai = json.loads(ai)
            rank = ai.get('investment_value', 'C')
            genre = ai.get('genre', 'その他')
            
            # カード全体を囲うコンテナ
            with st.container(border=True):
                # カスタムバッジ
                st.markdown(f"""
                    <div style="display: flex; gap: 5px; margin-bottom: 10px;">
                        <span class="rank-badge rank-{rank.lower()}">RANK {rank}</span>
                        <span class="genre-badge">{genre}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                if item['image_url']:
                    st.image(item['image_url'], use_container_width=True)
                
                st.markdown(f"#### {item['title']}")
                st.markdown(f"### <span style='color: #764ba2;'>¥{item['price']:,}</span>", unsafe_allow_html=True)
                
                with st.expander("📋 AI分析レポート"):
                    st.write(f"**📈 理由:** {ai.get('trend_reason', '分析中')}")
                    st.info(f"🔮 **将来予測:** {ai.get('future_prediction', '')}")
                
                st.link_button("商品ページを開く", item['product_url'], use_container_width=True)
                
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
    st.header("⚙️ 監視設定")
    db = DatabaseManager()
    
    c1, c2 = st.columns(2)
    with c1:
        with st.form("new_k"):
            st.subheader("キーワード追加")
            k = st.text_input("キーワード")
            p = st.number_input("目標利益", value=3000)
            if st.form_submit_button("保存") and k:
                db.supabase.table("search_configs").insert({"keyword": k, "target_profit": p}).execute()
                st.success(f"「{k}」を追加しました")
                st.rerun()
    with c2:
        st.subheader("一括操作")
        if st.button("🔥 Googleトレンドから自動取得"):
            subprocess.run([sys.executable, "trend_watcher.py"])
            st.rerun()

    st.divider()
    st.subheader("現在の監視リスト")
    configs = db.get_active_search_configs()
    if configs:
        st.dataframe(pd.DataFrame(configs)[['keyword', 'target_profit', 'created_at']], use_container_width=True)

def main():
    # サイドバー
    st.sidebar.title("🛠️ 管理設定")
    pw = st.sidebar.text_input("Admin Passphrase", type="password")
    is_admin = pw == os.environ.get("ADMIN_PASSWORD", "admin123")
    
    if is_admin:
        st.sidebar.success("管理者としてログイン中")
        if not os.environ.get("IS_CLOUD"):
            st.sidebar.divider()
            if is_bot_running():
                st.sidebar.success("ボット稼働中")
                if st.sidebar.button("ボットを停止"):
                    stop_bot()
            else:
                st.sidebar.error("ボット停止中")
                if st.sidebar.button("ボットを起動"):
                    start_bot()
    
    # メインタブ
    if is_admin:
        t_h, t_r, t_s = st.tabs(["🏠 ホーム", "🔎 リサーチ", "⚙️ 設定"])
        with t_h: show_about()
        with t_r: show_product_research(is_admin)
        with t_s: show_settings(is_admin)
    else:
        t_h, t_r = st.tabs(["🏠 ホーム", "🔎 リサーチ"])
        with t_h: show_about()
        with t_r: show_product_research(is_admin)

if __name__ == "__main__":
    main()
