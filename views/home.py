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


def calculate_volumes_breakdown(mangas: List[Manga], special_volume_service) -> dict:
    """漫画リストの冊数を詳細に分析（バッチ処理）
    
    Args:
        mangas: 漫画リスト
        special_volume_service: 特殊巻サービス
    
    Returns:
        dict: {
            'normal_volumes': 通常巻の合計,
            'special_volumes': 特殊巻の合計,
            'total_volumes': 全体の合計
        }
    """
    if not special_volume_service:
        normal_total = sum(manga.calculate_actual_owned_count() for manga in mangas)
        return {
            'normal_volumes': normal_total,
            'special_volumes': 0,
            'total_volumes': normal_total
        }
    
    # 特殊巻データを一括取得してキャッシュを構築
    try:
        special_volume_service.get_all_special_volumes_grouped_by_book()
    except Exception as e:
        print(f"Error caching special volumes: {e}")
    
    normal_total = 0
    special_total = 0
    
    for manga in mangas:
        # 通常巻の冊数
        normal_count = manga.calculate_actual_owned_count()
        normal_total += normal_count
        
        # 特殊巻の冊数（キャッシュから高速取得）
        special_count = special_volume_service.get_special_volume_count_for_book(manga.id)
        special_total += special_count
    
    return {
        'normal_volumes': normal_total,
        'special_volumes': special_total,
        'total_volumes': normal_total + special_total
    }

def calculate_total_volumes_with_specials(mangas: List[Manga], special_volume_service) -> int:
    """互換性のためのラッパー関数"""
    breakdown = calculate_volumes_breakdown(mangas, special_volume_service)
    return breakdown['total_volumes']


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
    if filters.get('title') and filters['title'].strip():
        title_query = filters['title'].lower()
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if title_query in manga.title.lower() or 
               (manga.title_kana and title_query in manga.title_kana.lower())
        ]
    
    # 雑誌タイプ検索（マルチセレクト対応）
    magazine_types_filter = filters.get('magazine_types', [])
    # 旧形式の互換性を維持
    if not magazine_types_filter and filters.get('magazine_type') and filters['magazine_type'] != 'すべて':
        magazine_types_filter = [filters['magazine_type']]
    
    if magazine_types_filter:
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if manga.magazine_type in magazine_types_filter
        ]
    
    # 雑誌名検索（部分一致）
    if filters.get('magazine_name') and filters['magazine_name'].strip():
        magazine_name_query = filters['magazine_name'].lower()
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if magazine_name_query in (manga.magazine_name or '').lower()
        ]
    
    # 連載状況検索
    if filters.get('completion_status') and filters['completion_status'] != 'すべて':
        is_completed_filter = filters['completion_status'] == '完結'
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if manga.is_completed == is_completed_filter
        ]
    
    # 未所持巻フィルター
    if filters.get('has_unpurchased') and filters['has_unpurchased'] != "すべて":
        if filters['has_unpurchased'] == "あり":
            filtered_mangas = [manga for manga in filtered_mangas if manga.has_unpurchased]
        elif filters['has_unpurchased'] == "なし":
            filtered_mangas = [manga for manga in filtered_mangas if not manga.has_unpurchased]
    
    # 所持媒体フィルター（マルチセレクト対応）
    owned_medias_filter = filters.get('owned_medias', [])
    # 旧形式の互換性を維持
    if not owned_medias_filter and filters.get('owned_media') and filters['owned_media'] != 'すべて':
        owned_medias_filter = [filters['owned_media']]
    
    if owned_medias_filter:
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if manga.owned_media in owned_medias_filter
        ]
    
    # 所持巻数範囲フィルター
    min_owned = filters.get('min_owned_volume', 0)
    max_owned = filters.get('max_owned_volume', 999)
    if min_owned > 0 or max_owned < 999:
        filtered_mangas = [
            manga for manga in filtered_mangas 
            if min_owned <= manga.actual_owned_volume <= max_owned
        ]
    
    # 重複削除完了
    
    return filtered_mangas


def show_books_home(
    manga_service: MangaService,
    notion_api_key: str,
    books_database_id: str,
    go_to_detail: callable,
    special_volume_service=None
):
    """Home画面：本の一覧を3列グリッド表示"""
    st.header("📖 所持作品一覧")
    
    # 新規登録ボタン
    st.markdown('<div class="add-book-button">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("➕ 新しい漫画を登録", type="primary"):
            st.session_state.page = "add_book"
            st.rerun()
    with col2:
        if st.button("📔 特殊巻を登録", type="secondary"):
            st.session_state.page = "add_special_volume"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
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
        
        # 検索結果件数と合計冊数を表示（特殊巻の内訳を含む）
        if any(search_filters.values()):
            # フィルター結果の分析
            filtered_breakdown = calculate_volumes_breakdown(filtered_mangas, special_volume_service)
            # 全体の分析
            all_breakdown = calculate_volumes_breakdown(mangas, special_volume_service)
            
            # 表示形式: 10作品・50冊の漫画が見つかりました（50/94作品・50冊[12冊]/1670冊[30冊]）
            filtered_total = filtered_breakdown['total_volumes']
            filtered_special = filtered_breakdown['special_volumes']
            all_total = all_breakdown['total_volumes']
            all_special = all_breakdown['special_volumes']
            
            st.info(f"🎯 {len(filtered_mangas)}作品・{filtered_total}冊の漫画が見つかりました（{len(filtered_mangas)}/{len(mangas)}作品・{filtered_total}冊[{filtered_special}冊]/{all_total}冊[{all_special}冊]）")
        else:
            # 全件表示時も特殊巻の内訳を表示
            breakdown = calculate_volumes_breakdown(mangas, special_volume_service)
            total_volumes = breakdown['total_volumes']
            special_volumes = breakdown['special_volumes']
            st.info(f"📚 全{len(mangas)}作品・{total_volumes}冊の漫画を表示中（特殊巻{special_volumes}冊を含む）")
        
        # 全ての漫画をtitle_kanaの五十音順でソート
        sorted_mangas = sorted(
            filtered_mangas,
            key=lambda m: m.title_kana or m.title or ""
        )
        
        # PC表示：3カラムで表示
        # スマホ表示：CSSで1カラムに変換
        for row_start in range(0, len(sorted_mangas), 3):
            cols = st.columns(3, gap="small")
            row_books = sorted_mangas[row_start:row_start + 3]
            
            for col_idx, manga in enumerate(row_books):
                with cols[col_idx]:
                    # BookCardコンポーネントでHTMLを生成
                    st.markdown(BookCard.render(manga), unsafe_allow_html=True)
                    
                    # 詳細ボタン
                    if st.button(f"詳細を見る", key=f"detail_{manga.id}", use_container_width=True):
                        go_to_detail(manga.to_dict())
                        st.rerun()
