"""
BookForm Component: 漫画登録・編集フォームの共通フィールド
"""

import streamlit as st
import datetime
from typing import Optional, Dict, Any, Tuple


class BookFormFields:
    """漫画登録・編集フォームの共通フィールドを提供するクラス"""
    
    @staticmethod
    def render_basic_info(
        default_title: str = "",
        default_title_kana: str = "",
        default_magazine_type: str = "ジャンプ",
        default_magazine_name: str = "",
        key_prefix: str = ""
    ) -> Dict[str, Any]:
        """
        基本情報セクションのフィールドを表示
        
        Args:
            default_title: タイトルのデフォルト値
            default_title_kana: タイトルかなのデフォルト値
            default_magazine_type: 連載誌タイプのデフォルト値
            default_magazine_name: 連載誌名のデフォルト値
        
        Returns:
            Dict[str, Any]: {title, title_kana, magazine_type, magazine_name}
        """
        st.subheader("📝 基本情報")
        
        # エンターキー送信を防ぐためのコールバック関数
        def prevent_enter_submit():
            pass
        
        title = st.text_input(
            "漫画タイトル *", 
            value=default_title, 
            placeholder="例: ONE PIECE",
            key=f"{key_prefix}title_input",
            on_change=prevent_enter_submit
        )
        title_kana = st.text_input(
            "タイトルかな（並び順用）",
            value=default_title_kana,
            placeholder="例: わんぴーす",
            help="空欄の場合は保存時に自動生成されます",
            key=f"{key_prefix}title_kana_input",
            on_change=prevent_enter_submit
        )
        
        magazine_types = ["ジャンプ", "マガジン", "サンデー", "その他"]
        try:
            magazine_type_index = magazine_types.index(default_magazine_type)
        except ValueError:
            magazine_type_index = 3  # "その他"
        
        magazine_type = st.selectbox("連載誌タイプ *", magazine_types, index=magazine_type_index)
        magazine_name = st.text_input(
            "連載誌名", 
            value=default_magazine_name, 
            placeholder="例: 週刊少年ジャンプ",
            key=f"{key_prefix}magazine_name_input",
            on_change=prevent_enter_submit
        )
        
        return {
            "title": title,
            "title_kana": title_kana,
            "magazine_type": magazine_type,
            "magazine_name": magazine_name
        }
    
    @staticmethod
    def render_series_selection(
        all_mangas: list = None,
        current_manga_id: str = None,
        default_parent_id: str = None,
        key_prefix: str = ""
    ) -> Dict[str, Any]:
        """
        シリーズ選択セクションのフィールドを表示
        
        Args:
            all_mangas: 全漫画データのリスト
            current_manga_id: 現在編集中の漫画ID（自己参照を避けるため）
            default_parent_id: デフォルトの親作品ID
            
        Returns:
            Dict[str, Any]: {parent_id: str|None}
        """
        st.subheader("🔗 シリーズ情報")
        
        parent_id = None
        
        if all_mangas:
            # 親作品になれる作品をフィルタリング
            # 1. 自分以外
            # 2. related_books_to が空の作品（親作品を持たない作品）
            # 3. 現在の親作品は編集時に選択肢に含める
            available_parents = []
            for manga in all_mangas:
                if manga.id == current_manga_id:
                    continue  # 自分は除外
                
                # 現在の親作品の場合は常に含める
                if manga.id == default_parent_id:
                    available_parents.append(manga)
                # それ以外は子作品を持たない作品のみ
                elif manga.related_books_to is None or len(manga.related_books_to) == 0:
                    available_parents.append(manga)
            
            if available_parents:
                # 検索機能付きプルダウン
                parent_options = ["なし"] + [f"{manga.title}" for manga in available_parents]
                parent_values = [None] + [manga.id for manga in available_parents]
                
                # 検索用テキストボックス（エンターキー送信防止）
                def prevent_enter_submit():
                    pass
                
                search_query = st.text_input(
                    "親作品を検索",
                    placeholder="作品タイトルで検索...",
                    help="この作品が続編・外伝・スピンオフの場合、元となる作品を選択",
                    key=f"{key_prefix}series_search_input",
                    on_change=prevent_enter_submit
                )
                
                # 検索結果でフィルタリング
                if search_query:
                    filtered_parents = [
                        manga for manga in available_parents 
                        if search_query.lower() in manga.title.lower() or 
                           search_query.lower() in (manga.title_kana or "").lower()
                    ]
                    filtered_options = ["なし"] + [f"{manga.title}" for manga in filtered_parents]
                    filtered_values = [None] + [manga.id for manga in filtered_parents]
                else:
                    filtered_options = parent_options
                    filtered_values = parent_values
                
                # デフォルト選択インデックスを計算
                default_parent_index = 0
                if default_parent_id and default_parent_id in filtered_values:
                    default_parent_index = filtered_values.index(default_parent_id)
                
                # 選択ボックス
                selected_parent_index = st.selectbox(
                    "親作品選択",
                    range(len(filtered_options)),
                    index=default_parent_index,
                    format_func=lambda x: filtered_options[x],
                    help="選択した作品の子作品として登録されます"
                )
                parent_id = filtered_values[selected_parent_index]
                
            else:
                st.info("📚 親作品にできる作品がありません")
        else:
            st.warning("⚠️ 作品データを読み込めませんでした")
        
        return {
            "parent_id": parent_id
        }
    
    @staticmethod
    def render_series_relation(
        all_mangas: list = None,
        current_manga_id: str = None,
        default_parent_id: str = None,
        default_children_ids: list = None
    ) -> Dict[str, Any]:
        """
        シリーズ関係設定セクションのフィールドを表示
        
        Args:
            all_mangas: 全漫画データのリスト（リレーション先選択用）
            current_manga_id: 現在編集中の漫画ID（自己参照を避けるため）
            default_parent_id: デフォルトの親作品ID
            default_children_ids: デフォルトの子作品IDリスト
            
        Returns:
            Dict[str, Any]: {parent_id: str|None, children_ids: list}
        """
        if default_children_ids is None:
            default_children_ids = []
            
        st.subheader("🔗 シリーズ関係")
        
        parent_id = None
        children_ids = []
        
        if all_mangas:
            # 自分以外の作品をフィルタリング
            available_mangas = [
                manga for manga in all_mangas 
                if manga.id != current_manga_id
            ]
            
            if available_mangas:
                # 親作品の選択
                parent_options = ["なし"] + [f"{manga.title}" for manga in available_mangas]
                parent_values = [None] + [manga.id for manga in available_mangas]
                
                default_parent_index = 0
                if default_parent_id:
                    try:
                        default_parent_index = parent_values.index(default_parent_id)
                    except ValueError:
                        pass
                
                selected_parent_index = st.selectbox(
                    "親作品（この作品の元となる作品）",
                    range(len(parent_options)),
                    index=default_parent_index,
                    format_func=lambda x: parent_options[x],
                    help="続編・外伝・スピンオフの場合、元となる作品を選択"
                )
                parent_id = parent_values[selected_parent_index]
                
                # 子作品の選択（複数選択）
                children_options = [manga for manga in available_mangas]
                default_children_indices = []
                if default_children_ids:
                    default_children_indices = [
                        i for i, manga in enumerate(children_options)
                        if manga.id in default_children_ids
                    ]
                
                selected_children_indices = st.multiselect(
                    "子作品（この作品から派生した作品）",
                    range(len(children_options)),
                    default=default_children_indices,
                    format_func=lambda x: children_options[x].title,
                    help="続編・外伝・スピンオフがある場合に選択"
                )
                children_ids = [children_options[i].id for i in selected_children_indices]
        
        return {
            "parent_id": parent_id,
            "children_ids": children_ids
        }
    
    @staticmethod
    def render_volume_info(
        default_owned: int = 1,
        default_released: int = 1
    ) -> Dict[str, int]:
        """
        巻数情報セクションのフィールドを表示
        
        Args:
            default_owned: 所持巻数のデフォルト値
            default_released: 発売済み巻数のデフォルト値
        
        Returns:
            Dict[str, int]: {latest_owned_volume, latest_released_volume}
        """
        col1, col2 = st.columns(2)
        with col1:
            latest_owned_volume = st.number_input(
                "現在所持巻数 *",
                min_value=0,
                value=default_owned
            )
        with col2:
            latest_released_volume = st.number_input(
                "発売済み最新巻 *",
                min_value=0,
                value=default_released
            )
        
        return {
            "latest_owned_volume": latest_owned_volume,
            "latest_released_volume": latest_released_volume
        }
    
    @staticmethod
    def render_image_info(
        current_image_url: Optional[str] = None,
        is_edit_mode: bool = False
    ) -> Optional[Any]:
        """
        画像情報セクションのフィールドを表示
        
        Args:
            current_image_url: 現在の画像URL（編集モードの場合）
            is_edit_mode: 編集モードかどうか
        
        Returns:
            Optional[Any]: アップロードされたファイル、またはNone
        """
        st.subheader("📷 画像情報")
        
        # 編集モードの場合、現在の画像を表示
        if is_edit_mode and current_image_url:
            st.image(current_image_url, caption="現在の画像", width=200)
        elif is_edit_mode:
            st.info("現在、画像が登録されていません")
        
        # ファイルアップローダー
        label = "新しい画像をアップロード" if is_edit_mode and current_image_url else "画像ファイルを選択"
        if is_edit_mode and current_image_url:
            label += "（画像を変更する場合のみ）"
        
        key = "edit_image_upload" if is_edit_mode else "add_image_upload"
        uploaded_file = st.file_uploader(
            label,
            type=["jpg", "jpeg", "png", "webp"],
            help="JPG、PNG、WEBP形式の画像ファイルをアップロードできます",
            key=key
        )
        
        # プレビュー表示
        if uploaded_file is not None:
            st.image(uploaded_file, caption="新しい画像プレビュー" if is_edit_mode else "アップロード予定の画像", width=200)
        
        return uploaded_file
    
    @staticmethod
    def render_completion_status(default_completed: bool = False) -> bool:
        """
        完結情報フィールドを表示
        
        Args:
            default_completed: 完結済みのデフォルト値
        
        Returns:
            bool: 完結済みかどうか
        """
        return st.checkbox("完結済み", value=default_completed)
    
    @staticmethod
    def render_date_info(
        default_latest_date: Optional[datetime.date] = None,
        default_next_date: Optional[datetime.date] = None
    ) -> Tuple[datetime.date, bool, Optional[datetime.date]]:
        """
        発売日情報セクションのフィールドを表示
        
        Args:
            default_latest_date: 最新巻発売日のデフォルト値
            default_next_date: 次巻発売予定日のデフォルト値
        
        Returns:
            Tuple[datetime.date, bool, Optional[datetime.date]]: 
                (latest_release_date, use_next_release_date, next_release_date)
        """
        st.subheader("📅 発売日情報")
        
        if default_latest_date is None:
            default_latest_date = datetime.date.today()
        
        latest_release_date = st.date_input(
            "最新巻発売日 *",
            value=default_latest_date,
            min_value=datetime.date(1960, 1, 1),
            max_value=datetime.date(2100, 12, 31),
            help="最新巻の発売日を設定します（必須項目）"
        )
        
        use_next_release_date = st.checkbox(
            "次巻発売予定日を登録する" if default_next_date is None else "次巻発売予定日を設定する",
            value=default_next_date is not None
        )
        
        if default_next_date is None:
            default_next_date = datetime.date.today() + datetime.timedelta(days=90)
        
        next_release_date = st.date_input(
            "次巻発売予定日",
            value=default_next_date,
            min_value=datetime.date(1960, 1, 1),
            max_value=datetime.date(2100, 12, 31),
            help="上のチェックボックスをオンにした場合のみ登録されます" if default_next_date is None else "上のチェックボックスをオンにした場合のみ保存されます"
        )
        
        return latest_release_date, use_next_release_date, next_release_date
    
    @staticmethod
    def render_detail_info(
        default_missing_volumes: str = "",
        default_special_volumes: str = "",
        default_owned_media: str = "単行本",
        default_notes: str = "",
        key_prefix: str = ""
    ) -> Dict[str, str]:
        """
        詳細情報セクションのフィールドを表示
        
        Args:
            default_missing_volumes: 未所持巻のデフォルト値
            default_special_volumes: 特殊巻のデフォルト値
            default_owned_media: 所持媒体のデフォルト値
            default_notes: 備考のデフォルト値
        
        Returns:
            Dict[str, str]: {missing_volumes, special_volumes, owned_media, notes}
        """
        st.subheader("📚 詳細情報")
        
        # エンターキー送信を防ぐためのコールバック関数
        def prevent_enter_submit():
            pass
        
        missing_volumes = st.text_input(
            "未所持巻（抜け）",
            value=default_missing_volumes,
            placeholder="例: 3,5,10",
            key=f"{key_prefix}missing_volumes_input",
            on_change=prevent_enter_submit
        )
        special_volumes = st.text_input(
            "特殊巻",
            value=default_special_volumes,
            placeholder="例: 10.5,外伝1",
            key=f"{key_prefix}special_volumes_input",
            on_change=prevent_enter_submit
        )
        
        media_options = ["単行本", "電子(ジャンプ+)", "電子(マガポケ)", "電子(U-NEXT)"]
        try:
            media_index = media_options.index(default_owned_media)
        except ValueError:
            media_index = 0
        
        owned_media = st.selectbox("所持媒体", media_options, index=media_index)
        notes = st.text_area("備考", value=default_notes, placeholder="その他メモ...")
        
        return {
            "missing_volumes": missing_volumes,
            "special_volumes": special_volumes,
            "owned_media": owned_media,
            "notes": notes
        }
    
    @staticmethod
    def render_search_filters() -> dict:
        """
        検索フィルター用のフィールドを表示
        
        Returns:
            dict: 検索条件の辞書
        """
        from utils.session import SessionManager
        
        # セッションから保存された検索条件を取得
        saved_filters = SessionManager.get_search_filters()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # エンターキー送信を防ぐためのコールバック関数
            def prevent_enter_submit():
                pass
                
            # タイトル検索
            title_search = st.text_input(
                "📚 タイトル検索",
                value=saved_filters.get("title", ""),
                placeholder="例: ワンピース",
                help="タイトルまたは読み仮名での部分一致検索",
                key="search_title_input",
                on_change=prevent_enter_submit
            )
            
            # 雑誌タイプ検索
            magazine_types = ["すべて", "ジャンプ", "マガジン", "サンデー", "その他"]
            saved_magazine_type = saved_filters.get("magazine_type", "すべて")
            magazine_type_index = magazine_types.index(saved_magazine_type) if saved_magazine_type in magazine_types else 0
            magazine_type_filter = st.selectbox(
                "📰 連載誌タイプ",
                magazine_types,
                index=magazine_type_index
            )
            
            # 雑誌名検索
            magazine_name_search = st.text_input(
                "📖 連載誌名",
                value=saved_filters.get("magazine_name", ""),
                placeholder="例: 週刊少年ジャンプ",
                help="連載誌名での部分一致検索",
                key="search_magazine_name_input",
                on_change=prevent_enter_submit
            )
        
        with col2:
            # 未所持巻フィルター
            has_unpurchased_options = ["すべて", "あり", "なし"]
            saved_has_unpurchased = saved_filters.get("has_unpurchased", "すべて")
            has_unpurchased_index = has_unpurchased_options.index(saved_has_unpurchased) if saved_has_unpurchased in has_unpurchased_options else 0
            has_unpurchased_filter = st.selectbox(
                "📋 未所持巻",
                has_unpurchased_options,
                index=has_unpurchased_index,
                help="未購入の巻があるかどうかで絞り込み"
            )
            
            # 所持媒体フィルター
            owned_media_options = ["すべて", "単行本", "電子(ジャンプ+)", "電子(マガポケ)", "電子(U-NEXT)"]
            saved_owned_media = saved_filters.get("owned_media", "すべて")
            owned_media_index = owned_media_options.index(saved_owned_media) if saved_owned_media in owned_media_options else 0
            owned_media_filter = st.selectbox(
                "💻 所持媒体",
                owned_media_options,
                index=owned_media_index
            )
            
            # 所持巻数範囲
            st.write("📊 所持巻数範囲")
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                min_owned = st.number_input(
                    "最小",
                    min_value=0,
                    max_value=999,
                    value=saved_filters.get("min_owned_volume", 0),
                    help="最小所持巻数"
                )
            with col2_2:
                max_owned = st.number_input(
                    "最大",
                    min_value=0,
                    max_value=999,
                    value=saved_filters.get("max_owned_volume", 999),
                    help="最大所持巻数"
                )
        
        # フィルター条件を辞書で返す
        filters = {
            'title': title_search.strip() if title_search else "",
            'magazine_type': magazine_type_filter if magazine_type_filter != "すべて" else "すべて",
            'magazine_name': magazine_name_search.strip() if magazine_name_search else "",
            'has_unpurchased': has_unpurchased_filter if has_unpurchased_filter != "すべて" else "すべて",
            'owned_media': owned_media_filter if owned_media_filter != "すべて" else "すべて",
            'min_owned_volume': min_owned if min_owned > 0 else 0,
            'max_owned_volume': max_owned if max_owned < 999 else 999
        }
        
        # セッションに検索条件を保存
        SessionManager.set_search_filters(filters)
        
        # クリアボタン
        if st.button("🗑️ フィルターをクリア", help="すべての検索条件をリセット"):
            SessionManager.clear_search_filters()
            st.rerun()
        
        return filters
