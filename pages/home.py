"""
Home Page: Book list display with grid layout
"""

import streamlit as st
from services.manga_service import MangaService
from services.image_service import ImageService
from components.book_card import BookCard
from utils.session import SessionManager
from config.constants import MAGAZINE_TYPE_ORDER, MAGAZINE_LOGOS


def show_books_home(
    manga_service: MangaService,
    notion_api_key: str,
    books_database_id: str,
    go_to_detail: callable
):
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
                if notion_api_key:
                    api_key_masked = f"{notion_api_key[:4]}...{notion_api_key[-4:]}" if len(notion_api_key) > 8 else "設定済み"
                    st.write(f"**APIキー**: {api_key_masked}")
                    st.write(f"**APIキー長**: {len(notion_api_key)}文字")
                else:
                    st.write("**APIキー**: 未設定")
                    
                if books_database_id:
                    db_id_masked = f"{books_database_id[:4]}...{books_database_id[-4:]}" if len(books_database_id) > 8 else "設定済み"
                    st.write(f"**データベースID**: {db_id_masked}")
                    st.write(f"**データベースID長**: {len(books_database_id)}文字")
                else:
                    st.write("**データベースID**: 未設定")
                    
                st.write(f"**エラー詳細**: {error_message}")
                
                # 設定ファイルの場所を表示
                st.markdown("**📁 設定ファイルの場所:**")
                st.code(".streamlit/secrets.toml")
                
                # 現在の設定値チェック
                if "your_notion_api_key_here" in notion_api_key:
                    st.error("❌ APIキーがデフォルト値のままです")
                if "your_books_database_id_here" in books_database_id:
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
        
        # magazine_typeごとに表示
        for magazine_type in MAGAZINE_TYPE_ORDER:
            if magazine_type in grouped_books:
                # アコーディオンヘッダー（クリック可能）
                is_expanded = st.session_state.magazine_type_expanded.get(magazine_type, True)
                expand_icon = "🔽" if is_expanded else "▶️"
                
                # ヘッダーボタン（ロゴは定数から取得）
                logo_url = MAGAZINE_LOGOS.get(magazine_type)

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
