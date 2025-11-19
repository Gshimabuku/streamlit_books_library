"""
DeleteDialog Component: 削除確認ダイアログ
"""

import streamlit as st
import time
from typing import Dict, Any, Callable
from services.manga_service import MangaService
from services.image_service import ImageService


class DeleteDialog:
    """削除確認ダイアログのUIと処理を担当するクラス"""
    
    @staticmethod
    def show(
        book: Dict[str, Any],
        manga_service: MangaService,
        image_service: ImageService,
        on_success_callback: Callable[[], None]
    ) -> None:
        """
        削除確認ダイアログを表示
        
        Args:
            book: 削除対象の漫画データ（dict形式）
            manga_service: MangaServiceインスタンス
            image_service: ImageServiceインスタンス
            on_success_callback: 削除成功時のコールバック関数
        """
        st.warning(f"**{book['title']}** を削除しますか？")
        st.error("⚠️ この操作は取り消せません。")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ 削除する", type="primary", use_container_width=True):
                DeleteDialog._handle_delete(book, manga_service, image_service, on_success_callback)
        
        with col2:
            if st.button("❌ キャンセル", use_container_width=True):
                st.rerun()
    
    @staticmethod
    def _handle_delete(
        book: Dict[str, Any],
        manga_service: MangaService,
        image_service: ImageService,
        on_success_callback: Callable[[], None]
    ) -> None:
        """
        削除処理を実行
        
        Args:
            book: 削除対象の漫画データ
            manga_service: MangaServiceインスタンス
            image_service: ImageServiceインスタンス
            on_success_callback: 削除成功時のコールバック関数
        """
        try:
            # ImageServiceを使用して画像削除
            image_url = book.get("image_url")
            if image_url:
                with st.spinner("画像を削除中..."):
                    if image_service.delete_image(image_url):
                        st.success("✅ 画像を削除しました")
            
            # MangaServiceを使用してNotionレコード削除
            with st.spinner("データを削除中..."):
                if manga_service.delete_manga(book["id"]):
                    st.success("✅ 漫画を削除しました")
                else:
                    raise Exception("削除に失敗しました")
            
            # セッション状態をクリア
            st.session_state.selected_book = None
            
            # 削除成功後、少し待ってからコールバック実行
            time.sleep(1)
            on_success_callback()
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 削除に失敗しました: {str(e)}")
