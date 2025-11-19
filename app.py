import streamlit as st
from utils.notion_client import query_notion, create_notion_page, update_notion_page, retrieve_notion_page, delete_notion_page
from utils.css_loader import load_custom_styles
from utils.kana_converter import title_to_kana
from utils.config import Config
from utils.session import SessionManager
from services.manga_service import MangaService
from services.image_service import ImageService
from models.manga import Manga
from components.book_card import BookCard
from components.book_form import BookFormFields
from components.delete_dialog import DeleteDialog
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
notion_config = Config.load_notion_config()
NOTION_API_KEY = notion_config["api_key"]
BOOKS_DATABASE_ID = notion_config["database_id"]

# =========================
# Cloudinary 設定
# =========================
cloudinary_config = Config.load_cloudinary_config()
if CLOUDINARY_AVAILABLE and cloudinary_config:
    try:
        cloudinary.config(
            cloud_name=cloudinary_config["cloud_name"],
            api_key=cloudinary_config["api_key"],
            api_secret=cloudinary_config["api_secret"]
        )
        CLOUDINARY_ENABLED = True
    except Exception:
        CLOUDINARY_ENABLED = False
else:
    CLOUDINARY_ENABLED = False

# =========================
# セッション状態の初期化
# =========================
SessionManager.init()

# =========================
# サービス層の初期化
# =========================
manga_service = MangaService(NOTION_API_KEY, BOOKS_DATABASE_ID)
image_service = ImageService(CLOUDINARY_AVAILABLE, CLOUDINARY_ENABLED)

# =========================
# ページ遷移関数（SessionManagerから取得）
# =========================
go_to_home = SessionManager.go_to_home
go_to_detail = SessionManager.go_to_detail
go_to_add_book = SessionManager.go_to_add_book
go_to_edit_book = SessionManager.go_to_edit_book

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
    st.header("📖 所持作品一覧")
    
    # 新規登録ボタン
    st.markdown('<div class="add-book-button">', unsafe_allow_html=True)
    if st.button("➕ 新しい漫画を登録", type="primary"):
        st.session_state.page = "add_book"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # データベース接続を試行
    mangas = []
    
    try:
        # MangaServiceを使用してデータを取得
        with st.spinner("データを読み込み中..."):
            mangas = manga_service.get_all_mangas()
        
        # データが取得できなかった場合
        if not mangas:
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
        mangas = []
    
    # 本の一覧表示（データがある場合のみ）
    if mangas:
        # MangaServiceを使用してグループ化
        grouped_books = manga_service.group_by_magazine(mangas)
        
        # magazine_typeの表示順序を定義
        type_order = ["ジャンプ", "マガジン", "サンデー", "その他"]
        
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
                    sorted_names = manga_service.sort_magazine_names(magazine_names, magazine_type)
                    
                    for magazine_name in sorted_names:
                        # magazine_nameヘッダー（BookCardコンポーネント使用）
                        st.markdown(BookCard.render_magazine_header(magazine_name), unsafe_allow_html=True)
                        
                        # この雑誌の本を表示
                        magazine_books = grouped_books[magazine_type][magazine_name]
                        
                        # PC表示：3カラムで表示
                        # スマホ表示：CSSで1カラムに変換（順序を保つため）
                        for row_start in range(0, len(magazine_books), 3):
                            cols = st.columns(3, gap="small")
                            row_books = magazine_books[row_start:row_start + 3]
                            
                            for col_idx, manga in enumerate(row_books):
                                with cols[col_idx]:
                                    # BookCardコンポーネントでHTMLを生成
                                    st.markdown(BookCard.render(manga), unsafe_allow_html=True)
                                    
                                    # 詳細ボタンを情報部分内に配置（スマホでは右側に表示）
                                    # Mangaオブジェクトをdict形式に変換してセッションに保存（後方互換性のため）
                                    if st.button(f"詳細を見る", key=f"detail_{manga.id}", use_container_width=True):
                                        go_to_detail(manga.to_dict())
                                        st.rerun()

@st.dialog("削除確認")
def confirm_delete_dialog():
    """削除確認ダイアログ（DeleteDialogコンポーネント使用）"""
    book = st.session_state.selected_book
    DeleteDialog.show(book, manga_service, image_service, go_to_home)

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
                missing_list = [vol.strip() for vol in missing_volumes.split(",") if vol.strip()]
                missing_count = len(missing_list)
                actual_owned = owned_count - missing_count
                st.write(f"**所持巻数:** {actual_owned}巻")
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
        # BookFormFieldsコンポーネントを使用
        basic_info = BookFormFields.render_basic_info()
        title = basic_info["title"]
        title_kana = basic_info["title_kana"]
        magazine_type = basic_info["magazine_type"]
        magazine_name = basic_info["magazine_name"]
        
        volume_info = BookFormFields.render_volume_info()
        latest_owned_volume = volume_info["latest_owned_volume"]
        latest_released_volume = volume_info["latest_released_volume"]
        
        uploaded_file = BookFormFields.render_image_info()
        
        # Cloudinaryが利用可能かチェック（プレビュー後のメッセージ）
        if uploaded_file is not None:
            if CLOUDINARY_ENABLED and CLOUDINARY_AVAILABLE:
                st.info("📤 登録時にCloudinaryにアップロードされます")
            else:
                st.warning("⚠️ Cloudinary設定が見つかりません。画像URLは保存されません。")
        
        is_completed = BookFormFields.render_completion_status()
        
        latest_release_date, use_next_release_date, next_release_date = BookFormFields.render_date_info()
        
        detail_info = BookFormFields.render_detail_info()
        missing_volumes = detail_info["missing_volumes"]
        special_volumes = detail_info["special_volumes"]
        owned_media = detail_info["owned_media"]
        notes = detail_info["notes"]
        
        # 登録ボタン
        submitted = st.form_submit_button("📚 漫画を登録", type="primary")
        
        if submitted:
            if not title or not magazine_type:
                st.error("❌ タイトルと連載誌タイプは必須項目です")
            elif latest_owned_volume > latest_released_volume:
                st.error("❌ 所持巻数が発売済み最新巻を超えています")
            else:
                try:
                    # ImageServiceを使用して画像アップロード
                    final_image_url = None
                    
                    if uploaded_file is not None and image_service.is_available():
                        with st.spinner("画像をアップロード中..."):
                            final_image_url = image_service.upload_image(uploaded_file)
                            st.success(f"✅ 画像アップロード完了: {uploaded_file.name}")
                    elif uploaded_file is not None:
                        st.warning("⚠️ Cloudinary設定がないため、画像はアップロードされませんでした")
                    
                    # タイトルかなを自動生成（未入力の場合）
                    final_title_kana = title_kana.strip() if title_kana else ""
                    ai_generated = False
                    
                    if not final_title_kana and title:
                        openai_api_key = Config.get_openai_api_key()
                        use_ai = openai_api_key is not None
                        ai_generated = use_ai
                        
                        with st.spinner("タイトルかなを生成中..." + (" (AI使用)" if use_ai else "")):
                            final_title_kana = title_to_kana(title, use_ai=use_ai, api_key=openai_api_key)
                    
                    # Mangaオブジェクトを作成
                    new_manga = Manga(
                        id=None,  # 新規登録なのでNone
                        title=title,
                        title_kana=final_title_kana,
                        magazine_type=magazine_type,
                        magazine_name=magazine_name,
                        latest_owned_volume=latest_owned_volume,
                        latest_released_volume=latest_released_volume,
                        is_completed=is_completed,
                        image_url=final_image_url,
                        latest_release_date=latest_release_date,
                        next_release_date=next_release_date if use_next_release_date else None,
                        missing_volumes=missing_volumes,
                        special_volumes=special_volumes,
                        owned_media=owned_media,
                        notes=notes
                    )
                    
                    # MangaServiceを使用して登録
                    try:
                        with st.spinner("Notionに登録中..."):
                            result_id = manga_service.create_manga(new_manga)
                        
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
    
    # 編集フォーム（BookFormFieldsコンポーネントを使用）
    with st.form("edit_book_form"):
        basic_info = BookFormFields.render_basic_info(
            default_title=current_title,
            default_title_kana=current_title_kana,
            default_magazine_type=current_magazine_type,
            default_magazine_name=current_magazine_name
        )
        title = basic_info["title"]
        title_kana = basic_info["title_kana"]
        magazine_type = basic_info["magazine_type"]
        magazine_name = basic_info["magazine_name"]
        
        volume_info = BookFormFields.render_volume_info(
            default_owned=current_owned,
            default_released=current_released
        )
        latest_owned_volume = volume_info["latest_owned_volume"]
        latest_released_volume = volume_info["latest_released_volume"]
        
        uploaded_file = BookFormFields.render_image_info(
            current_image_url=current_image_url,
            is_edit_mode=True
        )
        
        if uploaded_file is not None:
            if CLOUDINARY_ENABLED and CLOUDINARY_AVAILABLE:
                st.info("📤 保存時にCloudinaryにアップロードされ、現在の画像と入れ替わります")
            else:
                st.warning("⚠️ Cloudinary設定が見つかりません")
        
        is_completed = BookFormFields.render_completion_status(default_completed=current_completed)
        
        latest_release_date, use_next_release_date, next_release_date = BookFormFields.render_date_info(
            default_latest_date=current_latest_release_date,
            default_next_date=current_next_release_date
        )
        
        detail_info = BookFormFields.render_detail_info(
            default_missing_volumes=current_missing_volumes,
            default_special_volumes=current_special_volumes,
            default_owned_media=current_owned_media,
            default_notes=current_notes
        )
        missing_volumes = detail_info["missing_volumes"]
        special_volumes = detail_info["special_volumes"]
        owned_media = detail_info["owned_media"]
        notes = detail_info["notes"]
        
        # 更新ボタン
        submitted = st.form_submit_button("💾 変更を保存", type="primary")
        
        if submitted:
            if not title or not magazine_type:
                st.error("❌ タイトルと連載誌タイプは必須項目です")
            elif latest_owned_volume > latest_released_volume:
                st.error("❌ 所持巻数が発売済み最新巻を超えています")
            else:
                try:
                    # ImageServiceを使用して画像を置き換え
                    final_image_url = current_image_url
                    
                    if uploaded_file is not None and image_service.is_available():
                        with st.spinner("画像をアップロード中..."):
                            final_image_url = image_service.replace_image(current_image_url, uploaded_file)
                            st.success(f"✅ 画像アップロード完了: {uploaded_file.name}")
                    elif uploaded_file is not None:
                        st.warning("⚠️ Cloudinary設定がないため、画像はアップロードされませんでした")
                    
                    # タイトルかなを自動生成（未入力の場合）
                    final_title_kana = title_kana.strip() if title_kana else ""
                    ai_generated = False
                    
                    if not final_title_kana and title:
                        openai_api_key = Config.get_openai_api_key()
                        use_ai = openai_api_key is not None
                        ai_generated = use_ai
                        
                        with st.spinner("タイトルかなを生成中..." + (" (AI使用)" if use_ai else "")):
                            final_title_kana = title_to_kana(title, use_ai=use_ai, api_key=openai_api_key)
                    
                    # Mangaオブジェクトを作成
                    updated_manga = Manga(
                        id=book["id"],
                        title=title,
                        title_kana=final_title_kana,
                        magazine_type=magazine_type,
                        magazine_name=magazine_name,
                        latest_owned_volume=latest_owned_volume,
                        latest_released_volume=latest_released_volume,
                        is_completed=is_completed,
                        image_url=final_image_url,
                        latest_release_date=latest_release_date,
                        next_release_date=next_release_date if use_next_release_date else None,
                        missing_volumes=missing_volumes,
                        special_volumes=special_volumes,
                        owned_media=owned_media,
                        notes=notes
                    )
                    
                    # MangaServiceを使用して更新
                    try:
                        with st.spinner("Notionを更新中..."):
                            if manga_service.update_manga(updated_manga):
                        
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
                            else:
                                st.error("❌ 更新に失敗しました")
                        
                    except Exception as update_error:
                        st.error(f"❌ 更新処理でエラーが発生しました: {str(update_error)}")
                    
                except Exception as e:
                    st.error(f"❌ 更新処理でエラーが発生しました: {str(e)}")
    
    # フォーム外で更新成功状態をチェック
    if st.session_state.get("update_success", False):
        st.success("🎉 更新が完了しました！")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📖 詳細に戻る", type="primary", use_container_width=True):
                st.session_state.update_success = False
                # MangaServiceを使用して更新されたデータを再取得
                try:
                    updated_manga = manga_service.get_manga_by_id(book["id"])
                    if updated_manga:
                        st.session_state.selected_book = updated_manga.to_dict()
                except:
                    pass  # エラー時は古いデータのまま
                
                st.session_state.page = "book_detail"
                st.rerun()
        
        with col2:
            if st.button("📚 一覧に戻る", use_container_width=True):
                st.session_state.update_success = False
                go_to_home()
                st.rerun()

if __name__ == "__main__":
    main()
