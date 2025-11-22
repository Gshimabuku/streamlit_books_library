"""セッション状態管理"""
import streamlit as st
from typing import Optional, Any

class SessionManager:
    """セッション状態を管理するクラス"""
    
    @staticmethod
    def init():
        """セッション状態を初期化"""
        if "page" not in st.session_state:
            st.session_state.page = "books_home"
        
        if "selected_book" not in st.session_state:
            st.session_state.selected_book = None
        
        # magazine_type_expanded は使用しないため削除
        # タブメニュー方式では展開状態の管理が不要
        
        if "registration_success" not in st.session_state:
            st.session_state.registration_success = False
        
        if "update_success" not in st.session_state:
            st.session_state.update_success = False
    
    @staticmethod
    def set_page(page_name: str):
        """ページを設定
        
        Args:
            page_name: ページ名 (books_home, book_detail, add_book, edit_book)
        """
        st.session_state.page = page_name
    
    @staticmethod
    def get_page() -> str:
        """現在のページを取得
        
        Returns:
            str: 現在のページ名
        """
        return st.session_state.get("page", "books_home")
    
    @staticmethod
    def set_selected_book(book_data: Any):
        """選択された本を設定
        
        Args:
            book_data: 本のデータ（辞書またはMangaオブジェクト）
        """
        st.session_state.selected_book = book_data
    
    @staticmethod
    def get_selected_book() -> Optional[Any]:
        """選択された本を取得
        
        Returns:
            選択された本のデータ、または None
        """
        return st.session_state.get("selected_book")
    
    @staticmethod
    def clear_selected_book():
        """選択をクリア"""
        st.session_state.selected_book = None
    
    # タブメニュー方式では以下のメソッドは不要
    # @staticmethod
    # def toggle_magazine_type(magazine_type: str):
    # @staticmethod
    # def is_magazine_type_expanded(magazine_type: str) -> bool:
    
    @staticmethod
    def set_registration_success(success: bool):
        """登録成功フラグを設定"""
        st.session_state.registration_success = success
    
    @staticmethod
    def get_registration_success() -> bool:
        """登録成功フラグを取得"""
        return st.session_state.get("registration_success", False)
    
    @staticmethod
    def set_update_success(success: bool):
        """更新成功フラグを設定"""
        st.session_state.update_success = success
    
    @staticmethod
    def get_update_success() -> bool:
        """更新成功フラグを取得"""
        return st.session_state.get("update_success", False)
    
    # ページ遷移のヘルパー関数
    @staticmethod
    def go_to_home():
        """ホームに戻る"""
        SessionManager.set_page("books_home")
        SessionManager.clear_selected_book()
    
    @staticmethod
    def go_to_detail(book_data: Any):
        """詳細画面に遷移"""
        SessionManager.set_page("book_detail")
        SessionManager.set_selected_book(book_data)
    
    @staticmethod
    def go_to_add_book():
        """新規登録画面に遷移"""
        SessionManager.set_page("add_book")
    
    @staticmethod
    def go_to_edit_book():
        """編集画面に遷移"""
        SessionManager.set_page("edit_book")
