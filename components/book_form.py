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
        default_magazine_name: str = ""
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
        
        title = st.text_input("漫画タイトル *", value=default_title, placeholder="例: ONE PIECE")
        title_kana = st.text_input(
            "タイトルかな（並び順用）",
            value=default_title_kana,
            placeholder="例: わんぴーす",
            help="空欄の場合は保存時に自動生成されます"
        )
        
        magazine_types = ["ジャンプ", "マガジン", "サンデー", "その他"]
        try:
            magazine_type_index = magazine_types.index(default_magazine_type)
        except ValueError:
            magazine_type_index = 3  # "その他"
        
        magazine_type = st.selectbox("連載誌タイプ *", magazine_types, index=magazine_type_index)
        magazine_name = st.text_input("連載誌名", value=default_magazine_name, placeholder="例: 週刊少年ジャンプ")
        
        return {
            "title": title,
            "title_kana": title_kana,
            "magazine_type": magazine_type,
            "magazine_name": magazine_name
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
        default_notes: str = ""
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
        
        missing_volumes = st.text_input(
            "未所持巻（抜け）",
            value=default_missing_volumes,
            placeholder="例: 3,5,10"
        )
        special_volumes = st.text_input(
            "特殊巻",
            value=default_special_volumes,
            placeholder="例: 10.5,外伝1"
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
        col1, col2 = st.columns(2)
        
        with col1:
            # タイトル検索
            title_search = st.text_input(
                "📚 タイトル検索",
                placeholder="例: ワンピース",
                help="タイトルまたは読み仮名での部分一致検索"
            )
            
            # 雑誌タイプ検索
            magazine_types = ["すべて", "ジャンプ", "マガジン", "サンデー", "その他"]
            magazine_type_filter = st.selectbox(
                "📰 連載誌タイプ",
                magazine_types,
                index=0
            )
            
            # 雑誌名検索
            magazine_name_search = st.text_input(
                "📖 連載誌名",
                placeholder="例: 週刊少年ジャンプ",
                help="連載誌名での部分一致検索"
            )
        
        with col2:
            # 未所持巻フィルター
            has_unpurchased_options = ["すべて", "あり", "なし"]
            has_unpurchased_filter = st.selectbox(
                "📋 未所持巻",
                has_unpurchased_options,
                index=0,
                help="未購入の巻があるかどうかで絞り込み"
            )
            
            # 所持媒体フィルター
            owned_media_options = ["すべて", "単行本", "電子(ジャンプ+)", "電子(マガポケ)", "電子(U-NEXT)"]
            owned_media_filter = st.selectbox(
                "💻 所持媒体",
                owned_media_options,
                index=0
            )
            
            # 所持巻数範囲
            st.write("📊 所持巻数範囲")
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                min_owned = st.number_input(
                    "最小",
                    min_value=0,
                    max_value=999,
                    value=0,
                    help="最小所持巻数"
                )
            with col2_2:
                max_owned = st.number_input(
                    "最大",
                    min_value=0,
                    max_value=999,
                    value=999,
                    help="最大所持巻数"
                )
        
        # フィルター条件を辞書で返す
        filters = {
            'title': title_search.strip() if title_search else None,
            'magazine_type': magazine_type_filter if magazine_type_filter != "すべて" else None,
            'magazine_name': magazine_name_search.strip() if magazine_name_search else None,
            'has_unpurchased': has_unpurchased_filter if has_unpurchased_filter != "すべて" else None,
            'owned_media': owned_media_filter if owned_media_filter != "すべて" else None,
            'min_owned_volume': min_owned if min_owned > 0 else None,
            'max_owned_volume': max_owned if max_owned < 999 else None
        }
        
        # クリアボタン
        if st.button("🗑️ フィルターをクリア", help="すべての検索条件をリセット"):
            st.rerun()
        
        return filters
