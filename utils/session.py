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
        
        # 検索条件の初期化
        if "search_filters" not in st.session_state:
            st.session_state.search_filters = {
                "title": "",
                "magazine_type": "すべて",
                "magazine_name": ""
            }
        
        # スクロール制御フラグ
        if "should_scroll_to_top" not in st.session_state:
            st.session_state.should_scroll_to_top = False
    
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
    
    @staticmethod
    def set_search_filters(filters: dict):
        """検索条件を設定"""
        st.session_state.search_filters = filters
    
    @staticmethod
    def get_search_filters() -> dict:
        """検索条件を取得"""
        return st.session_state.get("search_filters", {
            "title": "",
            "magazine_type": "すべて", 
            "magazine_name": ""
        })
    
    @staticmethod
    def clear_search_filters():
        """検索条件をクリア"""
        st.session_state.search_filters = {
            "title": "",
            "magazine_type": "すべて",
            "magazine_name": ""
        }
    
    @staticmethod
    def set_scroll_to_top(should_scroll: bool = True):
        """スクロール位置をトップに戻すフラグを設定"""
        st.session_state.should_scroll_to_top = should_scroll
    
    @staticmethod
    def should_scroll_to_top() -> bool:
        """スクロール位置をトップに戻すべきかを確認"""
        return st.session_state.get("should_scroll_to_top", False)
    
    @staticmethod
    def reset_scroll_flag():
        """スクロールフラグをリセット"""
        st.session_state.should_scroll_to_top = False
    
    # ページ遷移のヘルパー関数
    @staticmethod
    def go_to_home():
        """ホームに戻る"""
        SessionManager.set_page("books_home")
        SessionManager.clear_selected_book()
        # 検索条件は維持する
    
    @staticmethod
    def go_to_detail(book_data: Any):
        """詳細画面に遷移"""
        SessionManager.set_page("book_detail")
        SessionManager.set_selected_book(book_data)
        SessionManager.set_scroll_to_top(True)
    
    @staticmethod
    def go_to_add_book():
        """新規登録画面に遷移"""
        SessionManager.set_page("add_book")
    
    @staticmethod
    def go_to_edit_book():
        """編集画面に遷移"""
        SessionManager.set_page("edit_book")
