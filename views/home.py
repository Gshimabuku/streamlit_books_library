"""
Home Page: Book list display with grid layout
"""

import streamlit as st
from services.manga_service import MangaService
from services.image_service import ImageService
from components.book_card import BookCard
from components.book_form import BookFormFields
from utils.session import SessionManager
from config.constants import MAGAZINE_TYPE_ORDER
from typing import List
from models.manga import Manga


def filter_mangas(mangas: List[Manga], filters: dict) -> List[Manga]:
    """
    検索条件に基づいて漫画リストをフィルタリング
    
    Args:
        mangas: フィルタリング対象の漫画リスト
        filters: フィルター条件の辞書
    
    Returns:
        List[Manga]: フィルタリング後の漫画リスト
    """
    filtered_mangas = mangas
    
    # タイトル検索（部分一致）
    if filters.get('title'):
        title_query = filters['title'].lower()
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if title_query in manga.title.lower() or 
               (manga.title_kana and title_query in manga.title_kana.lower())
        ]
    
    # 雑誌タイプ検索
    if filters.get('magazine_type') and filters['magazine_type'] != "すべて":
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if manga.magazine_type == filters['magazine_type']
        ]
    
    # 雑誌名検索（部分一致）
    if filters.get('magazine_name'):
        magazine_query = filters['magazine_name'].lower()
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if magazine_query in (manga.magazine_name or "").lower()
        ]
    
    # 未所持巻フィルター
    if filters.get('has_unpurchased') == "あり":
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if manga.has_unpurchased
        ]
    elif filters.get('has_unpurchased') == "なし":
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if not manga.has_unpurchased
        ]
    
    # 所持媒体検索
    if filters.get('owned_media') and filters['owned_media'] != "すべて":
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if manga.owned_media == filters['owned_media']
        ]
    
    # 所持巻数範囲検索
    if filters.get('min_owned_volume') is not None:
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if manga.actual_owned_volume >= filters['min_owned_volume']
        ]
    
    if filters.get('max_owned_volume') is not None:
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if manga.actual_owned_volume <= filters['max_owned_volume']
        ]
    
    return filtered_mangas


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
    
    # 検索フィルター
    with st.expander("🔍 検索・フィルター", expanded=False):
        search_filters = BookFormFields.render_search_filters()
    
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
        # 検索フィルターを適用
        filtered_mangas = filter_mangas(mangas, search_filters)
        
        if not filtered_mangas:
            st.info("🔍 検索条件に一致する漫画が見つかりませんでした。")
            return
        
        # 検索結果件数を表示
        if any(search_filters.values()):
            st.info(f"🎯 {len(filtered_mangas)}件の漫画が見つかりました（全{len(mangas)}件中）")
        
        # magazine_typeごとにグループ化（magazine_nameは使用しない）
        grouped_by_type = {}
        for manga in filtered_mangas:
            magazine_type = manga.magazine_type or "その他"
            if magazine_type not in grouped_by_type:
                grouped_by_type[magazine_type] = []
            grouped_by_type[magazine_type].append(manga)
        
        # 存在する雑誌タイプのみを取得し、タブ名にカウントを追加
        available_types = []
        tab_names = []
        for magazine_type in MAGAZINE_TYPE_ORDER:
            if magazine_type in grouped_by_type:
                available_types.append(magazine_type)
                manga_count = len(grouped_by_type[magazine_type])
                tab_names.append(f"📚 {magazine_type} ({manga_count})")
        
        # タブメニュー表示
        if available_types:
            tabs = st.tabs(tab_names)
            
            # 各タブの内容を表示
            for idx, (magazine_type, tab) in enumerate(zip(available_types, tabs)):
                with tab:
                    # このタイプの漫画をtitle_kanaの五十音順でソート
                    type_mangas = sorted(
                        grouped_by_type[magazine_type],
                        key=lambda m: m.title_kana or m.title or ""
                    )
                    
                    # PC表示：3カラムで表示
                    # スマホ表示：CSSで1カラムに変換
                    for row_start in range(0, len(type_mangas), 3):
                        cols = st.columns(3, gap="small")
                        row_books = type_mangas[row_start:row_start + 3]
                        
                        for col_idx, manga in enumerate(row_books):
                            with cols[col_idx]:
                                # BookCardコンポーネントでHTMLを生成
                                st.markdown(BookCard.render(manga), unsafe_allow_html=True)
                                
                                # 詳細ボタン
                                if st.button(f"詳細を見る", key=f"detail_{magazine_type}_{manga.id}", use_container_width=True):
                                    go_to_detail(manga.to_dict())
                                    st.rerun()
