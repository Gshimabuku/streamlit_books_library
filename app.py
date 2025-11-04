import streamlit as st
from utils.notion_client import query_notion, create_notion_page, update_notion_page, retrieve_notion_page
import datetime

# =========================
# アプリケーション設定
# =========================
st.set_page_config(
    page_title="Books Library",
    page_icon="📚",
    layout="wide"
)

# =========================
# Notion 設定
# =========================
NOTION_API_KEY = st.secrets["notion"]["api_key"]
BOOKS_DATABASE_ID = st.secrets["notion"]["books_database_id"]

# =========================
# セッション状態の初期化
# =========================
if "page" not in st.session_state:
    st.session_state.page = "books_home"

if "selected_book" not in st.session_state:
    st.session_state.selected_book = None

# =========================
# ページ遷移関数
# =========================
def go_to_home():
    st.session_state.page = "books_home"
    st.session_state.selected_book = None

def go_to_detail(book_data):
    st.session_state.page = "book_detail"
    st.session_state.selected_book = book_data

# =========================
# メインアプリケーション
# =========================
def main():
    st.title("📚 Books Library")
    
    # ページ遷移に基づいてコンテンツを表示
    if st.session_state.page == "books_home":
        show_books_home()
    elif st.session_state.page == "book_detail":
        show_book_detail()

def show_books_home():
    """Home画面：本の一覧を3列グリッド表示"""
    st.header("📖 漫画ライブラリ")
    
    # ダミーデータ（後でNotionDBから取得に変更）
    dummy_books = [
        {
            "id": "book1",
            "title": "進撃の巨人",
            "image_url": "https://via.placeholder.com/200x300/FF6B6B/FFFFFF?text=進撃の巨人",
            "latest_owned_volume": 32,
            "latest_released_volume": 34,
            "is_completed": True
        },
        {
            "id": "book2", 
            "title": "鬼滅の刃",
            "image_url": "https://via.placeholder.com/200x300/4ECDC4/FFFFFF?text=鬼滅の刃",
            "latest_owned_volume": 20,
            "latest_released_volume": 23,
            "is_completed": True
        },
        {
            "id": "book3",
            "title": "ワンピース",
            "image_url": "https://via.placeholder.com/200x300/45B7D1/FFFFFF?text=ワンピース",
            "latest_owned_volume": 105,
            "latest_released_volume": 108,
            "is_completed": False
        }
    ]
    
    # 3列グリッド表示
    cols = st.columns(3)
    
    for i, book in enumerate(dummy_books):
        col = cols[i % 3]
        
        with col:
            # 本の画像
            st.image(book["image_url"], use_container_width=True)
            
            # タイトル
            st.subheader(book["title"])
            
            # 所持状況
            owned = book["latest_owned_volume"]
            released = book["latest_released_volume"]
            completion_status = "完結" if book["is_completed"] else "連載中"
            
            st.write(f"📖 所持: {owned}/{released}巻")
            st.write(f"📊 状況: {completion_status}")
            
            # 詳細ボタン
            if st.button(f"詳細を見る", key=f"detail_{book['id']}"):
                go_to_detail(book)
                st.rerun()

def show_book_detail():
    """詳細画面：選択された本の詳細情報表示"""
    if st.session_state.selected_book is None:
        st.error("本が選択されていません")
        if st.button("ホームに戻る"):
            go_to_home()
            st.rerun()
        return
    
    book = st.session_state.selected_book
    
    # 戻るボタン
    if st.button("← ホームに戻る"):
        go_to_home()
        st.rerun()
    
    st.header(f"📚 {book['title']}")
    
    # 2列レイアウト
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(book["image_url"], width=300)
    
    with col2:
        st.subheader("📊 所持情報")
        st.write(f"**現在所持巻数:** {book['latest_owned_volume']}巻")
        st.write(f"**発売済み最新巻:** {book['latest_released_volume']}巻")
        st.write(f"**完結状況:** {'完結' if book['is_completed'] else '連載中'}")
        
        # 編集ボタン（今後実装）
        st.subheader("⚙️ 操作")
        if st.button("編集する"):
            st.info("編集機能は今後実装予定です")
        
        if st.button("削除する", type="secondary"):
            st.warning("削除機能は今後実装予定です")

if __name__ == "__main__":
    main()
