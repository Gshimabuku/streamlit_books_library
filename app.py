import streamlit as st
from utils.notion_client import query_notion, create_notion_page, update_notion_page, retrieve_notion_page, delete_notion_page
from utils.css_loader import load_custom_styles
from utils.kana_converter import title_to_kana
import datetime
import os

# Cloudinaryのインポート
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

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
try:
    NOTION_API_KEY = st.secrets["notion"]["api_key"]
    BOOKS_DATABASE_ID = st.secrets["notion"]["database_id"]
        
except Exception as e:
    st.error(f"🔧 **Notion設定エラー**: {str(e)}")
    st.markdown("""
    ### 📋 secrets.toml ファイルを確認してください
    
    `.streamlit/secrets.toml` ファイルに以下の形式で設定が必要です：
    
    ```toml
    [notion]
    api_key = "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    database_id = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ```
    """)
    st.stop()

# =========================
# Cloudinary 設定
# =========================
if CLOUDINARY_AVAILABLE:
    try:
        cloudinary.config(
            cloud_name=st.secrets["cloudinary"]["cloud_name"],
            api_key=st.secrets["cloudinary"]["api_key"],
            api_secret=st.secrets["cloudinary"]["api_secret"]
        )
        CLOUDINARY_ENABLED = True
    except Exception:
        CLOUDINARY_ENABLED = False
else:
    CLOUDINARY_ENABLED = False

# =========================
# セッション状態の初期化
# =========================
if "page" not in st.session_state:
    st.session_state.page = "books_home"

if "selected_book" not in st.session_state:
    st.session_state.selected_book = None

# アコーディオンメニューの展開状態を管理
if "magazine_type_expanded" not in st.session_state:
    st.session_state.magazine_type_expanded = {
        "ジャンプ": True,
        "マガジン": True, 
        "サンデー": True,
        "その他": True
    }

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
    # カスタムCSSを読み込み
    load_custom_styles()
    
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
    
    # 新規登録ボタン
    st.markdown('<div class="add-book-button">', unsafe_allow_html=True)
    if st.button("➕ 新しい漫画を登録", type="primary"):
        st.session_state.page = "add_book"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # データベース接続を試行
    books = []
    
    try:
        # NotionDBから実際のデータを取得
        with st.spinner("データを読み込み中..."):
            sorts = [
                {
                    "property": "magazine_type", 
                    "direction": "ascending"
                },
                {
                    "property": "magazine_name", 
                    "direction": "ascending"
                },
                {
                    "property": "title_kana", 
                    "direction": "ascending"
                },
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
                    
                    # 雑誌タイプ取得
                    magazine_type = "その他"
                    if props.get("magazine_type", {}).get("select"):
                        magazine_type = props["magazine_type"]["select"]["name"]
                    
                    # 雑誌名取得
                    magazine_name = "不明"
                    if props.get("magazine_name", {}).get("rich_text") and props["magazine_name"]["rich_text"]:
                        magazine_name = props["magazine_name"]["rich_text"][0]["text"]["content"]
                    
                    book_data = {
                        "id": page["id"],
                        "title": title,
                        "image_url": image_url,
                        "latest_owned_volume": latest_owned_volume,
                        "latest_released_volume": latest_released_volume,
                        "is_completed": is_completed,
                        "magazine_type": magazine_type,
                        "magazine_name": magazine_name,
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
        error_message = str(e)
        if "401" in error_message or "Unauthorized" in error_message:
            st.error("🔐 **認証エラー**: Notion APIキーまたはデータベースIDが正しくありません")
            
            # デバッグ情報を表示（APIキーの最初と最後の4文字のみ表示）
            with st.expander("🔍 デバッグ情報"):
                if NOTION_API_KEY:
                    api_key_masked = f"{NOTION_API_KEY[:4]}...{NOTION_API_KEY[-4:]}" if len(NOTION_API_KEY) > 8 else "設定済み"
                    st.write(f"**APIキー**: {api_key_masked}")
                    st.write(f"**APIキー長**: {len(NOTION_API_KEY)}文字")
                else:
                    st.write("**APIキー**: 未設定")
                    
                if BOOKS_DATABASE_ID:
                    db_id_masked = f"{BOOKS_DATABASE_ID[:4]}...{BOOKS_DATABASE_ID[-4:]}" if len(BOOKS_DATABASE_ID) > 8 else "設定済み"
                    st.write(f"**データベースID**: {db_id_masked}")
                    st.write(f"**データベースID長**: {len(BOOKS_DATABASE_ID)}文字")
                else:
                    st.write("**データベースID**: 未設定")
                    
                st.write(f"**エラー詳細**: {error_message}")
                
                # 設定ファイルの場所を表示
                st.markdown("**📁 設定ファイルの場所:**")
                st.code(".streamlit/secrets.toml")
                
                # 現在の設定値チェック
                if "your_notion_api_key_here" in NOTION_API_KEY:
                    st.error("❌ APIキーがデフォルト値のままです")
                if "your_books_database_id_here" in BOOKS_DATABASE_ID:
                    st.error("❌ データベースIDがデフォルト値のままです")
            
            st.markdown("""
            ### 🔧 解決方法
            
            現在、設定ファイルにプレースホルダー値が設定されています。以下の手順で実際の値を設定してください：
            
            #### 1. Notion Integration を作成
            - [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations) にアクセス
            - 「New integration」をクリック
            - 適当な名前を付けて作成
            - 「Internal Integration Token」をコピー（`secret_` で始まる長い文字列）
            
            #### 2. データベースIDを取得
            - Notionで対象のデータベースを開く
            - URLから32文字のIDを取得: `https://notion.so/workspace/DATABASE_ID?v=...`
            - または、データベースページで「Share」→「Copy link」からURLを取得
            
            #### 3. データベースにIntegrationを招待
            - データベース画面で「Share」をクリック
            - 作成したIntegration名を検索して招待
            
            #### 4. 設定ファイル (`.streamlit/secrets.toml`) を更新
            ```toml
            [notion]
            api_key = "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"    # 実際のAPIキー
            database_id = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"       # 実際のデータベースID（32文字）
            ```
            
            #### 5. 必要なデータベースプロパティ
            以下のプロパティがデータベースに必要です：
            - `title` (Title)
            - `magazine_type` (Select) - オプション：ジャンプ、マガジン、サンデー、その他
            - `magazine_name` (Rich text)
            - `latest_owned_volume` (Number)
            - `latest_released_volume` (Number)
            - `is_completed` (Checkbox)
            - `image_url` (URL)
            - `latest_release_date` (Date)
            """)
            
            # 設定ファイル編集用の展開可能セクション
            with st.expander("⚙️ 設定ファイル編集ヘルプ"):
                st.markdown("**現在の設定ファイル内容:**")
                try:
                    with open("/workspaces/streamlit_books_library/.streamlit/secrets.toml", "r") as f:
                        current_config = f.read()
                    st.code(current_config, language="toml")
                except Exception:
                    st.warning("設定ファイルが見つかりません")
                
                st.markdown("**✏️ 編集手順:**")
                st.markdown("""
                1. 左側のファイルエクスプローラーで `.streamlit/secrets.toml` を開く
                2. `your_notion_api_key_here` を実際のAPIキーに置き換え
                3. `your_books_database_id_here` を実際のデータベースIDに置き換え
                4. ファイルを保存（Ctrl+S）
                5. このページをリロード
                """)
        elif "403" in error_message or "Forbidden" in error_message:
            st.error("🚫 **アクセス権限エラー**: データベースへのアクセスが拒否されました")
            st.info("💡 Notionデータベースで「共有」→ インテグレーションを招待してください")
        else:
            st.warning(f"⚠️ NotionDBに接続できませんでした: {error_message}")
            st.info("📋 設定を確認してください。")
        
        # エラー時は空のリストを設定
        books = []
    
    # 本の一覧表示（データがある場合のみ）
    if books:
        # 本をmagazine_typeとmagazine_nameでグループ分け
        from collections import defaultdict
        
        # magazine_typeの表示順序を定義
        type_order = ["ジャンプ", "マガジン", "サンデー", "その他"]
        
        # magazine_nameの表示順序を定義
        magazine_name_order = {
            "ジャンプ": ["週刊少年ジャンプ", "週刊ヤングジャンプ", "ジャンプ+", "ジャンプSQ", "ジャンプGIGA"],
            "マガジン": ["週刊少年マガジン", "週刊ヤングマガジン", "月刊少年マガジン", "別冊少年マガジン"],
            "サンデー": ["週刊少年サンデー", "少年サンデーＳ（スーパー）", "裏サンデー"],
            "その他": ["週刊ビッグコミックスピリッツ", "月刊コミックゼノン", "月刊アフタヌーン"]
        }
        
        # グループ分け用の辞書
        grouped_books = defaultdict(lambda: defaultdict(list))
        
        for book in books:
            magazine_type = book.get("magazine_type", "その他")
            magazine_name = book.get("magazine_name", "不明")
            grouped_books[magazine_type][magazine_name].append(book)
        
        # magazine_typeごとに表示
        for magazine_type in type_order:
            if magazine_type in grouped_books:
                # アコーディオンヘッダー（クリック可能）
                is_expanded = st.session_state.magazine_type_expanded.get(magazine_type, True)
                expand_icon = "🔽" if is_expanded else "▶️"
                
                # ヘッダーボタン（ロゴ画像 + ボタン）
                # 各雑誌タイプに対応するロゴ画像URL（必要に応じて差し替えてください）
                # ロゴをローカル静的ファイルから参照するように変更
                magazine_type_logos = {
                    "ジャンプ": "static/logos/jump.png",
                    "マガジン": "static/logos/magazine.png",
                    "サンデー": "static/logos/sunday.png",
                }

                logo_url = magazine_type_logos.get(magazine_type)

                # ヘッダーボタン（テキスト表示に戻す）
                if st.button(f"{expand_icon} 📚 {magazine_type} ({len(grouped_books[magazine_type])}誌)",
                             key=f"toggle_{magazine_type}",
                             use_container_width=True):
                    st.session_state.magazine_type_expanded[magazine_type] = not is_expanded
                    st.rerun()
                
                # 展開されている場合のみ内容を表示
                if is_expanded:
                    # magazine_nameをカスタム順序でソート
                    magazine_names = list(grouped_books[magazine_type].keys())
                    defined_order = magazine_name_order.get(magazine_type, [])
                    
                    # 定義済みの順序に従って並び替え、その後は辞書順
                    sorted_names = []
                    # まず定義済みの順序で追加
                    for name in defined_order:
                        if name in magazine_names:
                            sorted_names.append(name)
                    # 定義されていない雑誌名は辞書順で末尾に追加
                    remaining_names = [name for name in magazine_names if name not in defined_order]
                    sorted_names.extend(sorted(remaining_names))
                    
                    for magazine_name in sorted_names:
                        # magazine_nameヘッダー
                        st.markdown(f'<div class="magazine-name-header">📖 {magazine_name}</div>', unsafe_allow_html=True)
                        
                        # この雑誌の本を表示
                        magazine_books = grouped_books[magazine_type][magazine_name]
                        cols = st.columns(3, gap="small")
                        
                        for i, book in enumerate(magazine_books):
                            col = cols[i % 3]
                            
                            with col:
                                owned = book["latest_owned_volume"]
                                released = book["latest_released_volume"]
                                completion_status = "完結" if book["is_completed"] else "連載中"
                                
                                # 未購入巻の判定
                                has_unpurchased = owned < released
                                unpurchased_badge = '<span class="unpurchased-badge">未購入あり</span>' if has_unpurchased else ""
                    
                                # 画像HTMLを準備
                                try:
                                    if book["image_url"] and book["image_url"] != "":
                                        image_html = f'<img src="{book["image_url"]}" alt="{book["title"]}">'  
                                    else:
                                        image_html = '<img src="https://res.cloudinary.com/do6trtdrp/image/upload/v1762307174/noimage_czluse.jpg" alt="画像なし">'  
                                except:
                                    image_html = '<img src="https://res.cloudinary.com/do6trtdrp/image/upload/v1762307174/noimage_czluse.jpg" alt="画像読み込みエラー">'                                # 本のカード全体をHTMLで作成
                                st.markdown(f"""
                                <div class="book-card">
                                    <div class="mobile-book-image">
                                        {image_html}
                                    </div>
                                    <div class="mobile-book-info">
                                        <div class="status-container">
                                            <span class="status-badge {'status-completed' if book['is_completed'] else 'status-ongoing'}">{completion_status}</span>{unpurchased_badge}
                                        </div>
                                        <h3>{book["title"]}</h3>
                                        <div class="book-volume-info">
                                            📖 {owned}/{released}巻
                                        </div>
                                        <div class="detail-button-container">
                                            <!-- ボタンはStreamlitコンポーネントで配置 -->
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # 詳細ボタンを情報部分内に配置（スマホでは右側に表示）
                                if st.button(f"詳細を見る", key=f"detail_{book['id']}", use_container_width=True):
                                    go_to_detail(book)
                                    st.rerun()

@st.dialog("削除確認")
def confirm_delete_dialog():
    """削除確認ダイアログ"""
    book = st.session_state.selected_book
    
    st.warning(f"**{book['title']}** を削除しますか？")
    st.error("⚠️ この操作は取り消せません。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ 削除する", type="primary", use_container_width=True):
            try:
                # Cloudinary画像の削除
                image_url = book.get("image_url")
                if image_url and CLOUDINARY_ENABLED:
                    try:
                        # CloudinaryのURLからpublic_idを抽出
                        if "cloudinary.com" in image_url:
                            import re
                            match = re.search(r'/upload/(?:v\d+/)?([^/]+?)(?:\.[^.]+)?$', image_url)
                            if match:
                                public_id = match.group(1)
                                with st.spinner("画像を削除中..."):
                                    cloudinary.uploader.destroy(public_id)
                                st.success("✅ 画像を削除しました")
                    except Exception as img_error:
                        st.warning(f"⚠️ 画像の削除に失敗しました: {str(img_error)}")
                
                # Notionレコードの削除
                with st.spinner("データを削除中..."):
                    delete_notion_page(book["id"], NOTION_API_KEY)
                
                st.success("✅ 漫画を削除しました")
                
                # セッション状態をクリア
                st.session_state.selected_book = None
                
                # ホームに戻る
                import time
                time.sleep(1)
                go_to_home()
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ 削除に失敗しました: {str(e)}")
    
    with col2:
        if st.button("❌ キャンセル", use_container_width=True):
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
    
    # ボタン群を水平配置（PC右揃え、モバイル横並び）
    st.markdown('<div class="detail-buttons-container">', unsafe_allow_html=True)
    
    # 3列レイアウト（戻る・空白・編集削除）
    home_col, spacer_col, action_col = st.columns([2, 1, 2])
    
    with home_col:
        if st.button("← ホームに戻る"):
            go_to_home()
            st.rerun()
    
    with action_col:
        # 編集・削除ボタンを入れ子の列で右揃え配置
        edit_col, delete_col = st.columns(2)
        with edit_col:
            if st.button("✏️ 編集"):
                go_to_edit_book()
                st.rerun()
        with delete_col:
            if st.button("🗑️ 削除", type="secondary"):
                confirm_delete_dialog()
    
    st.markdown('</div>', unsafe_allow_html=True)  # detail-buttons-container終了
    
    # Notionから詳細データを取得
    page_data = book.get("page_data", {})
    props = page_data.get("properties", {})
    
    # 追加情報を取得
    latest_release_date = ""
    if props.get("latest_release_date", {}).get("date"):
        latest_release_date = props["latest_release_date"]["date"]["start"]
    
    next_release_date = ""
    if props.get("next_release_date", {}).get("date"):
        next_release_date = props["next_release_date"]["date"]["start"]
    
    missing_volumes = ""
    if props.get("missing_volumes", {}).get("rich_text") and props["missing_volumes"]["rich_text"]:
        missing_volumes = props["missing_volumes"]["rich_text"][0]["text"]["content"]
    
    special_volumes = ""
    if props.get("special_volumes", {}).get("rich_text") and props["special_volumes"]["rich_text"]:
        special_volumes = props["special_volumes"]["rich_text"][0]["text"]["content"]
    
    # 2列レイアウト
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 画像表示（エラーハンドリング付き）
        try:
            if book["image_url"] and book["image_url"] != "":
                st.image(book["image_url"], width=300)
            else:
                st.image("https://res.cloudinary.com/do6trtdrp/image/upload/v1762307174/noimage_czluse.jpg", width=300)
        except Exception as e:
            st.image("https://res.cloudinary.com/do6trtdrp/image/upload/v1762307174/noimage_czluse.jpg", width=300)
    
    with col2:
        # タイトル
        st.header(f"📚 {book['title']}")
        
        # 漫画情報
        completion_status = "完結" if book['is_completed'] else "連載中"
        
        # 完結・連載中のステータスを背景色付きで表示
        if book['is_completed']:
            status_color = "#28a745"  # 緑色（完結）
            text_color = "white"
        else:
            status_color = "#007bff"  # 青色（連載中）
            text_color = "white"
        
        status_class = "status-completed" if book['is_completed'] else "status-ongoing"
        st.markdown(f"""
        <div class="detail-status-badge {status_class}">
            {completion_status}
        </div>
        """, unsafe_allow_html=True)
        
        # 最新巻情報
        release_info = f"**最新巻:** {book['latest_released_volume']}巻"
        if latest_release_date:
            from datetime import datetime
            try:
                date_obj = datetime.strptime(latest_release_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%Y年%m月%d日")
                release_info += f" [{formatted_date}発売]"
            except:
                release_info += f" [{latest_release_date}発売]"
        st.write(release_info)
        
        # 次巻発売日
        if next_release_date:
            try:
                date_obj = datetime.strptime(next_release_date, "%Y-%m-%d")
                formatted_next_date = date_obj.strftime("%Y年%m月%d日")
                st.write(f"**次巻発売日:** {formatted_next_date}")
            except:
                st.write(f"**次巻発売日:** {next_release_date}")
        
        st.markdown("---")
        
        # 所持状況
        st.subheader("📚 所持状況")
        
        # 所持巻数の計算
        owned_count = book['latest_owned_volume']
        missing_count = 0
        
        # 抜け巻がある場合の計算
        if missing_volumes:
            try:
                missing_list = [vol.strip() for vol in missing_volumes.split(",")]
                missing_count = len(missing_list)
                actual_owned = owned_count - missing_count
                st.write(f"**所持巻数:** {owned_count}巻 ({actual_owned}巻)")
            except:
                st.write(f"**所持巻数:** {owned_count}巻")
        else:
            st.write(f"**所持巻数:** {owned_count}巻")
        
        # 抜け巻
        if missing_volumes:
            st.write(f"**抜け巻:** {missing_volumes}")
        
        # 特殊巻
        if special_volumes:
            st.write(f"**特殊巻:** {special_volumes}")

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
        title = st.text_input("漫画タイトル *", placeholder="例: ONE PIECE")
        title_kana = st.text_input(
            "タイトルかな（並び順用）", 
            placeholder="例: わんぴーす",
            help="空欄の場合は保存時に自動生成されます"
        )
        
        magazine_type = st.selectbox("連載誌タイプ *", ["ジャンプ", "マガジン", "サンデー", "その他"])
        magazine_name = st.text_input("連載誌名", placeholder="例: 週刊少年ジャンプ")
        
        # 巻数情報
        col1, col2 = st.columns(2)
        with col1:
            latest_owned_volume = st.number_input("現在所持巻数 *", min_value=0, value=1)
        with col2:
            latest_released_volume = st.number_input("発売済み最新巻 *", min_value=0, value=1)
        
        # その他情報
        st.subheader("📷 画像情報")
        
        uploaded_file = st.file_uploader(
            "画像ファイルを選択", 
            type=["jpg", "jpeg", "png", "webp"],
            help="JPG、PNG、WEBP形式の画像ファイルをアップロードできます"
        )
        
        if uploaded_file is not None:
            # プレビュー表示
            st.image(uploaded_file, caption="アップロード予定の画像", width=200)
            
            # Cloudinaryが利用可能かチェック
            if CLOUDINARY_ENABLED and CLOUDINARY_AVAILABLE:
                st.info("📤 登録時にCloudinaryにアップロードされます")
            else:
                st.warning("⚠️ Cloudinary設定が見つかりません。画像URLは保存されません。")
        
        # 完結情報
        is_completed = st.checkbox("完結済み")
        
        # 日付情報
        st.subheader("📅 発売日情報")
        
        # 最新巻発売日
        latest_release_date = st.date_input(
            "最新巻発売日 *",
            value=datetime.date.today(),
            min_value=datetime.date(1960, 1, 1),
            max_value=datetime.date(2100, 12, 31),
            help="最新巻の発売日を設定します（必須項目）"
        )
        
        # 次巻発売予定日
        use_next_release_date = st.checkbox("次巻発売予定日を登録する")
        next_release_date = st.date_input(
            "次巻発売予定日",
            value=datetime.date.today() + datetime.timedelta(days=90),
            min_value=datetime.date(1960, 1, 1),
            max_value=datetime.date(2100, 12, 31),
            help="上のチェックボックスをオンにした場合のみ登録されます"
        )
        
        # 詳細情報
        st.subheader("📚 詳細情報")
        missing_volumes = st.text_input("未所持巻（抜け）", placeholder="例: 3,5,10")
        special_volumes = st.text_input("特殊巻", placeholder="例: 10.5,外伝1")
        owned_media = st.selectbox("所持媒体", ["単行本", "電子(ジャンプ+)", "電子(マガポケ)", "電子(U-NEXT)"])
        notes = st.text_area("備考", placeholder="その他メモ...")
        
        # 登録ボタン
        submitted = st.form_submit_button("📚 漫画を登録", type="primary")
        
        if submitted:
            if not title or not magazine_type:
                st.error("❌ タイトルと連載誌タイプは必須項目です")
            else:
                try:
                    # 画像アップロード処理
                    final_image_url = None
                    
                    if uploaded_file is not None:
                        if CLOUDINARY_ENABLED and CLOUDINARY_AVAILABLE:
                            with st.spinner("画像をアップロード中..."):
                                upload_result = cloudinary.uploader.upload(uploaded_file)
                                final_image_url = upload_result["secure_url"]
                                st.success(f"✅ 画像アップロード完了: {uploaded_file.name}")
                        else:
                            st.warning("⚠️ Cloudinary設定がないため、画像はアップロードされませんでした")
                    
                    # Notionページのプロパティ構築
                    properties = {
                        "title": {"title": [{"text": {"content": title}}]},
                        "latest_owned_volume": {"number": latest_owned_volume},
                        "latest_released_volume": {"number": latest_released_volume},
                        "latest_release_date": {"date": {"start": latest_release_date.isoformat()}},
                        "is_completed": {"checkbox": is_completed}
                    }
                    
                    # タイトルかなを追加（未入力の場合はAIで自動生成）
                    final_title_kana = title_kana.strip() if title_kana else ""
                    ai_generated = False
                    
                    if not final_title_kana and title:
                        # AI APIキーを取得（secrets.tomlまたは環境変数から）
                        openai_api_key = None
                        try:
                            openai_api_key = st.secrets.get("openai", {}).get("api_key") or os.environ.get("OPENAI_API_KEY")
                        except:
                            pass
                        
                        # AIを使用して変換（APIキーがある場合）
                        use_ai = openai_api_key is not None
                        ai_generated = use_ai
                        
                        with st.spinner("タイトルかなを生成中..." + (" (AI使用)" if use_ai else "")):
                            final_title_kana = title_to_kana(title, use_ai=use_ai, api_key=openai_api_key)
                    
                    if final_title_kana:
                        properties["title_kana"] = {"rich_text": [{"text": {"content": final_title_kana}}]}
                    
                    # 次巻発売予定日
                    if use_next_release_date and next_release_date:
                        properties["next_release_date"] = {"date": {"start": next_release_date.isoformat()}}
                    
                    # 追加プロパティ
                    if magazine_type:
                        properties["magazine_type"] = {"select": {"name": magazine_type}}
                    
                    if magazine_name:
                        properties["magazine_name"] = {"rich_text": [{"text": {"content": magazine_name}}]}
                    
                    if missing_volumes:
                        properties["missing_volumes"] = {"rich_text": [{"text": {"content": missing_volumes}}]}
                    
                    if special_volumes:
                        properties["special_volumes"] = {"rich_text": [{"text": {"content": special_volumes}}]}
                    
                    if owned_media:
                        properties["owned_media"] = {"select": {"name": owned_media}}
                    
                    if notes:
                        properties["notes"] = {"rich_text": [{"text": {"content": notes}}]}
                    
                    # 画像URL
                    if final_image_url:
                        properties["image_url"] = {"url": final_image_url}
                    
                    # 登録試行
                    try:
                        with st.spinner("Notionに登録中..."):
                            result = create_notion_page(BOOKS_DATABASE_ID, properties, NOTION_API_KEY)
                        
                        st.success("✅ 漫画が正常に登録されました！")
                        st.balloons()
                        
                        # 画像URLがある場合は表示
                        if final_image_url:
                            st.markdown(f"🔗 [画像を開く]({final_image_url})")
                        
                        # かなが自動生成された場合は通知（AI生成の場合は明示）
                        if not title_kana.strip() and final_title_kana:
                            if ai_generated:
                                st.info(f"🤖 タイトルかなをAIで生成しました: **{final_title_kana}** (AI生成)")
                            else:
                                st.info(f"💡 タイトルかなを自動生成しました: {final_title_kana}")
                        
                        # セッション状態で登録成功をマーク
                        st.session_state.registration_success = True
                        
                    except Exception as full_error:
                        st.error(f"❌ 登録に失敗しました: {str(full_error)}")
                        
                        # 最小限のプロパティで再試行
                        st.warning("� 基本プロパティのみで再試行します...")
                        
                        minimal_properties = {
                            "title": {"title": [{"text": {"content": title}}]},
                            "latest_owned_volume": {"number": latest_owned_volume},
                            "latest_released_volume": {"number": latest_released_volume},
                            "is_completed": {"checkbox": is_completed},
                            "latest_release_date": {"date": {"start": latest_release_date.isoformat()}}
                        }
                        
                        try:
                            with st.spinner("基本プロパティで登録中..."):
                                result = create_notion_page(BOOKS_DATABASE_ID, minimal_properties, NOTION_API_KEY)
                            
                            st.success("✅ 基本プロパティで登録成功！")
                            st.info("💡 基本情報のみ保存されました。詳細情報は後で編集してください。")
                            
                            # セッション状態で登録成功をマーク
                            st.session_state.registration_success = True
                            
                        except Exception as minimal_error:
                            st.error(f"❌ 基本プロパティでも登録失敗: {str(minimal_error)}")
                            st.info("💡 Notionデータベースのプロパティ設定を確認してください。")
                    
                except Exception as e:
                    st.error(f"❌ 登録処理でエラーが発生しました: {str(e)}")
    # フォーム外で登録成功状態をチェック
    if st.session_state.get("registration_success", False):
        st.success("🎉 登録が完了しました！")
        if st.button("📚 ホームに戻る", type="primary"):
            st.session_state.registration_success = False
            go_to_home()
            st.rerun()

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
    page_data = book.get("page_data", {})
    props = page_data.get("properties", {})
    
    # 既存データを取得
    current_title = book.get("title", "")
    current_magazine_type = book.get("magazine_type", "その他")
    
    # 雑誌名
    current_magazine_name = ""
    if props.get("magazine_name", {}).get("rich_text") and props["magazine_name"]["rich_text"]:
        current_magazine_name = props["magazine_name"]["rich_text"][0]["text"]["content"]
    
    # タイトルかな
    current_title_kana = ""
    if props.get("title_kana", {}).get("rich_text") and props["title_kana"]["rich_text"]:
        current_title_kana = props["title_kana"]["rich_text"][0]["text"]["content"]
    
    # 巻数情報
    current_owned = book.get("latest_owned_volume", 0)
    current_released = book.get("latest_released_volume", 0)
    current_completed = book.get("is_completed", False)
    
    # 画像URL
    current_image_url = book.get("image_url", "")
    
    # 発売日情報
    current_latest_release_date = datetime.date.today()
    if props.get("latest_release_date", {}).get("date"):
        try:
            date_str = props["latest_release_date"]["date"]["start"]
            current_latest_release_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            pass
    
    current_next_release_date = None
    if props.get("next_release_date", {}).get("date"):
        try:
            date_str = props["next_release_date"]["date"]["start"]
            current_next_release_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            pass
    
    # 詳細情報
    current_missing_volumes = ""
    if props.get("missing_volumes", {}).get("rich_text") and props["missing_volumes"]["rich_text"]:
        current_missing_volumes = props["missing_volumes"]["rich_text"][0]["text"]["content"]
    
    current_special_volumes = ""
    if props.get("special_volumes", {}).get("rich_text") and props["special_volumes"]["rich_text"]:
        current_special_volumes = props["special_volumes"]["rich_text"][0]["text"]["content"]
    
    current_owned_media = "単行本"
    if props.get("owned_media", {}).get("select"):
        current_owned_media = props["owned_media"]["select"]["name"]
    
    current_notes = ""
    if props.get("notes", {}).get("rich_text") and props["notes"]["rich_text"]:
        current_notes = props["notes"]["rich_text"][0]["text"]["content"]
    
    # 編集フォーム
    with st.form("edit_book_form"):
        st.subheader("📝 基本情報")
        
        # 必須項目
        title = st.text_input("漫画タイトル *", value=current_title)
        title_kana = st.text_input(
            "タイトルかな（並び順用）", 
            value=current_title_kana,
            placeholder="例: しんげきのきょじん",
            help="空欄の場合は保存時に自動生成されます"
        )
        
        magazine_type = st.selectbox(
            "連載誌タイプ *", 
            ["ジャンプ", "マガジン", "サンデー", "その他"],
            index=["ジャンプ", "マガジン", "サンデー", "その他"].index(current_magazine_type) if current_magazine_type in ["ジャンプ", "マガジン", "サンデー", "その他"] else 3
        )
        magazine_name = st.text_input("連載誌名", value=current_magazine_name)
        
        # 巻数情報
        col1, col2 = st.columns(2)
        with col1:
            latest_owned_volume = st.number_input("現在所持巻数 *", min_value=0, value=current_owned)
        with col2:
            latest_released_volume = st.number_input("発売済み最新巻 *", min_value=0, value=current_released)
        
        # その他情報
        st.subheader("📷 画像情報")
        
        # 現在の画像を表示
        if current_image_url:
            st.image(current_image_url, caption="現在の画像", width=200)
        else:
            st.info("現在、画像が登録されていません")
        
        uploaded_file = st.file_uploader(
            "新しい画像をアップロード" + ("（画像を変更する場合のみ）" if current_image_url else ""), 
            type=["jpg", "jpeg", "png", "webp"],
            help="JPG、PNG、WEBP形式の画像ファイルをアップロードできます",
            key="edit_image_upload"
        )
        
        if uploaded_file is not None:
            st.image(uploaded_file, caption="新しい画像プレビュー", width=200)
            if CLOUDINARY_ENABLED and CLOUDINARY_AVAILABLE:
                st.info("📤 保存時にCloudinaryにアップロードされ、現在の画像と入れ替わります")
            else:
                st.warning("⚠️ Cloudinary設定が見つかりません")
        
        # 完結情報
        is_completed = st.checkbox("完結済み", value=current_completed)
        
        # 日付情報
        st.subheader("📅 発売日情報")
        
        latest_release_date = st.date_input(
            "最新巻発売日 *",
            value=current_latest_release_date,
            min_value=datetime.date(1960, 1, 1),
            max_value=datetime.date(2100, 12, 31)
        )
        
        use_next_release_date = st.checkbox("次巻発売予定日を設定する", value=current_next_release_date is not None)
        next_release_date = st.date_input(
            "次巻発売予定日",
            value=current_next_release_date if current_next_release_date else datetime.date.today() + datetime.timedelta(days=90),
            min_value=datetime.date(1960, 1, 1),
            max_value=datetime.date(2100, 12, 31),
            help="上のチェックボックスをオンにした場合のみ保存されます"
        )
        
        # 詳細情報
        st.subheader("📚 詳細情報")
        missing_volumes = st.text_input("未所持巻（抜け）", value=current_missing_volumes, placeholder="例: 3,5,10")
        special_volumes = st.text_input("特殊巻", value=current_special_volumes, placeholder="例: 10.5,外伝1")
        owned_media = st.selectbox(
            "所持媒体", 
            ["単行本", "電子(ジャンプ+)", "電子(マガポケ)", "電子(U-NEXT)"],
            index=["単行本", "電子(ジャンプ+)", "電子(マガポケ)", "電子(U-NEXT)"].index(current_owned_media) if current_owned_media in ["単行本", "電子(ジャンプ+)", "電子(マガポケ)", "電子(U-NEXT)"] else 0
        )
        notes = st.text_area("備考", value=current_notes, placeholder="その他メモ...")
        
        # 更新ボタン
        submitted = st.form_submit_button("💾 変更を保存", type="primary")
        
        if submitted:
            if not title or not magazine_type:
                st.error("❌ タイトルと連載誌タイプは必須項目です")
            else:
                try:
                    # 画像アップロード処理
                    final_image_url = current_image_url  # デフォルトは現在の画像
                    
                    if uploaded_file is not None:
                        if CLOUDINARY_ENABLED and CLOUDINARY_AVAILABLE:
                            with st.spinner("画像をアップロード中..."):
                                upload_result = cloudinary.uploader.upload(uploaded_file)
                                final_image_url = upload_result["secure_url"]
                                st.success(f"✅ 画像アップロード完了: {uploaded_file.name}")
                                
                                # 古い画像を削除（Cloudinaryの場合）
                                if current_image_url and "cloudinary.com" in current_image_url:
                                    try:
                                        import re
                                        match = re.search(r'/upload/(?:v\d+/)?([^/]+?)(?:\.[^.]+)?$', current_image_url)
                                        if match:
                                            old_public_id = match.group(1)
                                            cloudinary.uploader.destroy(old_public_id)
                                    except:
                                        pass  # 古い画像削除失敗は無視
                        else:
                            st.warning("⚠️ Cloudinary設定がないため、画像はアップロードされませんでした")
                    
                    # Notionページのプロパティ構築
                    properties = {
                        "title": {"title": [{"text": {"content": title}}]},
                        "latest_owned_volume": {"number": latest_owned_volume},
                        "latest_released_volume": {"number": latest_released_volume},
                        "latest_release_date": {"date": {"start": latest_release_date.isoformat()}},
                        "is_completed": {"checkbox": is_completed}
                    }
                    
                    # タイトルかなを追加（未入力の場合はAIで自動生成）
                    final_title_kana = title_kana.strip() if title_kana else ""
                    ai_generated = False
                    
                    if not final_title_kana and title:
                        # AI APIキーを取得（secrets.tomlまたは環境変数から）
                        openai_api_key = None
                        try:
                            openai_api_key = st.secrets.get("openai", {}).get("api_key") or os.environ.get("OPENAI_API_KEY")
                        except:
                            pass
                        
                        # AIを使用して変換（APIキーがある場合）
                        use_ai = openai_api_key is not None
                        ai_generated = use_ai
                        
                        with st.spinner("タイトルかなを生成中..." + (" (AI使用)" if use_ai else "")):
                            final_title_kana = title_to_kana(title, use_ai=use_ai, api_key=openai_api_key)
                    
                    if final_title_kana:
                        properties["title_kana"] = {"rich_text": [{"text": {"content": final_title_kana}}]}
                    
                    # 次巻発売予定日
                    if use_next_release_date and next_release_date:
                        properties["next_release_date"] = {"date": {"start": next_release_date.isoformat()}}
                    else:
                        # チェックを外した場合は削除
                        properties["next_release_date"] = {"date": None}
                    
                    # 追加プロパティ
                    if magazine_type:
                        properties["magazine_type"] = {"select": {"name": magazine_type}}
                    
                    if magazine_name:
                        properties["magazine_name"] = {"rich_text": [{"text": {"content": magazine_name}}]}
                    else:
                        properties["magazine_name"] = {"rich_text": []}
                    
                    if missing_volumes:
                        properties["missing_volumes"] = {"rich_text": [{"text": {"content": missing_volumes}}]}
                    else:
                        properties["missing_volumes"] = {"rich_text": []}
                    
                    if special_volumes:
                        properties["special_volumes"] = {"rich_text": [{"text": {"content": special_volumes}}]}
                    else:
                        properties["special_volumes"] = {"rich_text": []}
                    
                    if owned_media:
                        properties["owned_media"] = {"select": {"name": owned_media}}
                    
                    if notes:
                        properties["notes"] = {"rich_text": [{"text": {"content": notes}}]}
                    else:
                        properties["notes"] = {"rich_text": []}
                    
                    # 画像URL
                    if final_image_url:
                        properties["image_url"] = {"url": final_image_url}
                    
                    # Notion更新
                    try:
                        with st.spinner("Notionを更新中..."):
                            result = update_notion_page(book["id"], properties, NOTION_API_KEY)
                        
                        st.success("✅ 漫画情報が正常に更新されました！")
                        st.balloons()
                        
                        # かなが自動生成された場合は通知（AI生成の場合は明示）
                        if not title_kana.strip() and final_title_kana:
                            if ai_generated:
                                st.info(f"🤖 タイトルかなをAIで生成しました: **{final_title_kana}** (AI生成)")
                            else:
                                st.info(f"💡 タイトルかなを自動生成しました: {final_title_kana}")
                        
                        # セッション状態で更新成功をマーク
                        st.session_state.update_success = True
                        
                    except Exception as update_error:
                        st.error(f"❌ 更新に失敗しました: {str(update_error)}")
                    
                except Exception as e:
                    st.error(f"❌ 更新処理でエラーが発生しました: {str(e)}")
    
    # フォーム外で更新成功状態をチェック
    if st.session_state.get("update_success", False):
        st.success("🎉 更新が完了しました！")
        if st.button("📖 詳細に戻る", type="primary"):
            st.session_state.update_success = False
            # 更新されたデータを再取得して詳細画面に戻る
            try:
                updated_page = retrieve_notion_page(book["id"], NOTION_API_KEY)
                # book_dataを更新
                updated_props = updated_page["properties"]
                
                updated_title = "タイトル不明"
                if updated_props.get("title", {}).get("title"):
                    updated_title = updated_props["title"]["title"][0]["text"]["content"]
                
                updated_image_url = updated_props.get("image_url", {}).get("url")
                if not updated_image_url or not updated_image_url.startswith(('http://', 'https://')):
                    updated_image_url = None
                
                updated_book_data = {
                    "id": book["id"],
                    "title": updated_title,
                    "image_url": updated_image_url,
                    "latest_owned_volume": updated_props.get("latest_owned_volume", {}).get("number", 0),
                    "latest_released_volume": updated_props.get("latest_released_volume", {}).get("number", 0),
                    "is_completed": updated_props.get("is_completed", {}).get("checkbox", False),
                    "magazine_type": updated_props.get("magazine_type", {}).get("select", {}).get("name", "その他"),
                    "magazine_name": updated_props.get("magazine_name", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "不明") if updated_props.get("magazine_name", {}).get("rich_text") else "不明",
                    "page_data": updated_page
                }
                
                st.session_state.selected_book = updated_book_data
            except:
                pass  # エラー時は古いデータのまま
            
            st.session_state.page = "book_detail"
            st.rerun()

if __name__ == "__main__":
    main()
