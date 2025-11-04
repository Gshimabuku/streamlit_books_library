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
BOOKS_DATABASE_ID = st.secrets["notion"]["database_id"]

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

def go_to_add_book():
    st.session_state.page = "add_book"

def go_to_edit_book():
    st.session_state.page = "edit_book"

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
    elif st.session_state.page == "add_book":
        show_add_book()
    elif st.session_state.page == "edit_book":
        show_edit_book()

def show_books_home():
    """Home画面：本の一覧を3列グリッド表示"""
    st.header("📖 漫画ライブラリ")
    
    # 新規登録ボタン（常に表示）
    if st.button("➕ 新しい漫画を登録", type="primary"):
        st.session_state.page = "add_book"
        st.rerun()
    
    st.markdown("---")
    
    # データベース接続を試行（エラーでも継続）
    books = []
    
    try:
        # NotionDBから実際のデータを取得
        with st.spinner("データを読み込み中..."):
            sorts = [
                {
                    "property": "title", 
                    "direction": "ascending"
                }
            ]
            results = query_notion(BOOKS_DATABASE_ID, NOTION_API_KEY, sorts=sorts)
            
            # NotionDBのデータを表示用に変換
            for page in results:
                try:
                    props = page["properties"]
                    
                    # タイトル取得
                    title = "タイトル不明"
                    if props.get("title", {}).get("title"):
                        title = props["title"]["title"][0]["text"]["content"]
                    
                    # 画像URL取得
                    image_url = props.get("image_url", {}).get("url")
                    # 無効なURLの場合はNoneに設定
                    if not image_url or not image_url.startswith(('http://', 'https://')):
                        image_url = None
                    
                    # 巻数情報取得
                    latest_owned_volume = props.get("latest_owned_volume", {}).get("number", 0)
                    latest_released_volume = props.get("latest_released_volume", {}).get("number", 0)
                    
                    # 完結情報取得
                    is_completed = props.get("is_completed", {}).get("checkbox", False)
                    
                    book_data = {
                        "id": page["id"],
                        "title": title,
                        "image_url": image_url,
                        "latest_owned_volume": latest_owned_volume,
                        "latest_released_volume": latest_released_volume,
                        "is_completed": is_completed,
                        "page_data": page  # 詳細表示用に元データも保持
                    }
                    books.append(book_data)
                    
                except Exception as e:
                    st.error(f"データ読み込みエラー: {str(e)}")
                    continue
        
        # NotionDBから取得できなかった場合
        if not books:
            st.info("💡 まだ漫画が登録されていません。「新しい漫画を登録」ボタンから追加してください。")
        
    except Exception as e:
        st.warning(f"⚠️ NotionDBに接続できませんでした: {str(e)}")
        st.info("📋 ダミーデータを表示しています。実際の使用時はNotionの設定を確認してください。")
        
        # エラー時はダミーデータを表示
        books = [
            {
                "id": "book1",
                "title": "進撃の巨人",
                "image_url": None,  # 安全な画像URLに変更
                "latest_owned_volume": 32,
                "latest_released_volume": 34,
                "is_completed": True
            },
            {
                "id": "book2", 
                "title": "鬼滅の刃",
                "image_url": None,  # 安全な画像URLに変更
                "latest_owned_volume": 20,
                "latest_released_volume": 23,
                "is_completed": True
            },
            {
                "id": "book3",
                "title": "ワンピース",
                "image_url": None,  # 安全な画像URLに変更
                "latest_owned_volume": 105,
                "latest_released_volume": 108,
                "is_completed": False
            }
        ]
    
    # 本の一覧表示（データがある場合のみ）
    if books:
        # 3列グリッド表示
        cols = st.columns(3)
        
        for i, book in enumerate(books):
            col = cols[i % 3]
            
            with col:
                # 本の画像（エラーハンドリング付き）
                try:
                    if book["image_url"] and book["image_url"] != "":
                        st.image(book["image_url"], use_container_width=True)
                    else:
                        # 画像がない場合はテキストで代替
                        st.markdown(f"""
                        <div style="
                            width: 100%; 
                            height: 300px; 
                            background-color: #f0f0f0; 
                            display: flex; 
                            align-items: center; 
                            justify-content: center; 
                            border-radius: 8px;
                            color: #666;
                            font-size: 14px;
                        ">
                            📚 画像なし
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    # 画像読み込みエラー時の代替表示
                    st.markdown(f"""
                    <div style="
                        width: 100%; 
                        height: 300px; 
                        background-color: #f8f8f8; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        border-radius: 8px;
                        color: #999;
                        font-size: 12px;
                    ">
                        ⚠️ 画像読み込みエラー
                    </div>
                    """, unsafe_allow_html=True)
                
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
        # 画像表示（エラーハンドリング付き）
        try:
            if book["image_url"] and book["image_url"] != "":
                st.image(book["image_url"], width=300)
            else:
                st.markdown(f"""
                <div style="
                    width: 300px; 
                    height: 400px; 
                    background-color: #f0f0f0; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    border-radius: 8px;
                    color: #666;
                    font-size: 16px;
                ">
                    📚 画像なし
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"""
            <div style="
                width: 300px; 
                height: 400px; 
                background-color: #f8f8f8; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                border-radius: 8px;
                color: #999;
                font-size: 14px;
            ">
                ⚠️ 画像読み込みエラー
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📊 所持情報")
        st.write(f"**現在所持巻数:** {book['latest_owned_volume']}巻")
        st.write(f"**発売済み最新巻:** {book['latest_released_volume']}巻")
        st.write(f"**完結状況:** {'完結' if book['is_completed'] else '連載中'}")
        
        # 編集ボタン（今後実装）
        st.subheader("⚙️ 操作")
        if st.button("編集する"):
            go_to_edit_book()
            st.rerun()
        
        if st.button("削除する", type="secondary"):
            if st.session_state.get("confirm_delete", False):
                try:
                    # 削除機能の実装（今後）
                    st.success("削除機能は今後実装予定です")
                    st.session_state.confirm_delete = False
                except Exception as e:
                    st.error(f"削除に失敗しました: {str(e)}")
            else:
                st.session_state.confirm_delete = True
                st.warning("⚠️ 本当に削除しますか？もう一度「削除する」ボタンを押してください。")
                st.rerun()

def show_add_book():
    """新規漫画登録画面"""
    st.header("➕ 新しい漫画を登録")
    
    # 戻るボタン
    if st.button("← ホームに戻る"):
        go_to_home()
        st.rerun()
    
    with st.form("add_book_form"):
        st.subheader("📝 基本情報")
        
        # 必須項目
        title = st.text_input("漫画タイトル *", placeholder="例: 進撃の巨人")
        magazine_type = st.selectbox("連載誌タイプ *", ["ジャンプ", "マガジン", "サンデー", "その他"])
        magazine_name = st.text_input("連載誌名", placeholder="例: 週刊少年マガジン")
        
        # 巻数情報
        col1, col2 = st.columns(2)
        with col1:
            latest_owned_volume = st.number_input("現在所持巻数 *", min_value=0, value=1)
        with col2:
            latest_released_volume = st.number_input("発売済み最新巻 *", min_value=0, value=1)
        
        # その他情報
        image_url = st.text_input("画像URL", placeholder="https://example.com/image.jpg")
        synopsis = st.text_area("あらすじ", placeholder="漫画のあらすじを入力...")
        
        # 完結情報
        is_completed = st.checkbox("完結済み")
        
        # 日付情報
        col3, col4 = st.columns(2)
        with col3:
            latest_release_date = st.date_input("最新巻発売日")
        with col4:
            next_release_date = st.date_input("次巻発売予定日")
        
        # 詳細情報
        st.subheader("📚 詳細情報")
        missing_volumes = st.text_input("未所持巻（抜け）", placeholder="例: 3,5,10")
        special_volumes = st.text_input("特殊巻", placeholder="例: 0.5,10.5")
        owned_media = st.selectbox("所持媒体", ["単行本", "電子書籍", "両方"])
        notes = st.text_area("備考", placeholder="その他メモ...")
        
        # 登録ボタン
        submitted = st.form_submit_button("📚 漫画を登録", type="primary")
        
        if submitted:
            if not title or not magazine_type:
                st.error("❌ タイトルと連載誌タイプは必須項目です")
            else:
                try:
                    # Notionページのプロパティ構築
                    properties = {
                        "title": {"title": [{"text": {"content": title}}]},
                        "magazine_type": {"rich_text": [{"text": {"content": magazine_type}}]},
                        "magazine_name": {"rich_text": [{"text": {"content": magazine_name or ""}}]},
                        "latest_owned_volume": {"number": latest_owned_volume},
                        "latest_released_volume": {"number": latest_released_volume},
                        "is_completed": {"checkbox": is_completed}
                    }
                    
                    # オプション項目の追加
                    if image_url:
                        properties["image_url"] = {"url": image_url}
                    if synopsis:
                        properties["synopsis"] = {"rich_text": [{"text": {"content": synopsis}}]}
                    if latest_release_date:
                        properties["latest_release_date"] = {"date": {"start": latest_release_date.isoformat()}}
                    if next_release_date:
                        properties["next_release_date"] = {"date": {"start": next_release_date.isoformat()}}
                    if missing_volumes:
                        properties["missing_volumes"] = {"rich_text": [{"text": {"content": missing_volumes}}]}
                    if special_volumes:
                        properties["special_volumes"] = {"rich_text": [{"text": {"content": special_volumes}}]}
                    if owned_media:
                        properties["owned_media"] = {"rich_text": [{"text": {"content": owned_media}}]}
                    if notes:
                        properties["notes"] = {"rich_text": [{"text": {"content": notes}}]}
                    
                    with st.spinner("登録中..."):
                        create_notion_page(BOOKS_DATABASE_ID, properties, NOTION_API_KEY)
                    
                    st.success("✅ 漫画が正常に登録されました！")
                    st.balloons()
                    
                    # 少し待ってからホームに戻る
                    import time
                    time.sleep(2)
                    go_to_home()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 登録に失敗しました: {str(e)}")

def show_edit_book():
    """漫画編集画面"""
    st.header("✏️ 漫画情報を編集")
    
    # 戻るボタン
    if st.button("← 詳細に戻る"):
        st.session_state.page = "book_detail"
        st.rerun()
    
    if st.session_state.selected_book is None:
        st.error("編集する漫画が選択されていません")
        return
    
    book = st.session_state.selected_book
    
    st.info("📝 編集機能は今後実装予定です")
    st.write(f"選択中の漫画: **{book['title']}**")

if __name__ == "__main__":
    main()
