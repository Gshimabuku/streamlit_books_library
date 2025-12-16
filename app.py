"""
Main Application: Router for Books Library
"""

import streamlit as st
from utils.css_loader import load_custom_styles
from utils.config import Config
from utils.session import SessionManager
from services.manga_service import MangaService
from services.image_service import ImageService
from services.special_volume_service import SpecialVolumeService
from components.delete_dialog import DeleteDialog

# ビューモジュールをインポート
from views.home import show_books_home
from views.detail import show_book_detail
from views.add import show_add_book
from views.edit import show_edit_book
from views.add_special_volume import show_add_special_volume

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
    layout="wide",
    initial_sidebar_state="collapsed"  # サイドバーを非表示
)

# =========================
# Notion 設定
# =========================
notion_config = Config.load_notion_config()
NOTION_API_KEY = notion_config["api_key"]
BOOKS_DATABASE_ID = notion_config["books_database_id"]
SPECIAL_VOLUMES_DATABASE_ID = notion_config["special_volumes_database_id"]

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
SessionManager.initialize()

# =========================
# サービス層の初期化
# =========================
manga_service = MangaService(NOTION_API_KEY, BOOKS_DATABASE_ID)
image_service = ImageService(CLOUDINARY_AVAILABLE, CLOUDINARY_ENABLED)
special_volume_service = SpecialVolumeService(NOTION_API_KEY, SPECIAL_VOLUMES_DATABASE_ID)

# =========================
# ページ遷移関数（SessionManagerから取得）
# =========================
go_to_home = SessionManager.go_to_home
go_to_detail = SessionManager.go_to_detail
go_to_add_book = SessionManager.go_to_add_book
go_to_edit_book = SessionManager.go_to_edit_book

go_to_add_special_volume = SessionManager.go_to_add_special_volume


# =========================
# 削除確認ダイアログ
# =========================
@st.dialog("削除確認")
def confirm_delete_dialog():
    """削除確認ダイアログ（DeleteDialogコンポーネント使用）"""
    book = st.session_state.selected_book
    DeleteDialog.show(book, manga_service, image_service, go_to_home)


# =========================
# メインアプリケーション
# =========================
def main():
    """メインルーター: 現在のページに応じて適切な画面を表示"""
    # カスタムCSSを読み込み
    load_custom_styles()
    
    # 現在のページに応じてルーティング
    current_page = st.session_state.page
    
    if current_page == "books_home":
        show_books_home(
            manga_service=manga_service,
            notion_api_key=NOTION_API_KEY,
            books_database_id=BOOKS_DATABASE_ID,
            go_to_detail=go_to_detail,
            special_volume_service=special_volume_service
        )
    
    elif current_page == "book_detail":
        show_book_detail(special_volume_service)
    
    elif current_page == "add_book":
        show_add_book(
            manga_service=manga_service,
            image_service=image_service,
            go_to_home=go_to_home,
            notion_api_key=NOTION_API_KEY,
            books_database_id=BOOKS_DATABASE_ID,
            cloudinary_available=CLOUDINARY_AVAILABLE,
            cloudinary_enabled=CLOUDINARY_ENABLED
        )
    
    elif current_page == "edit_book":
        show_edit_book(
            manga_service=manga_service,
            image_service=image_service,
            go_to_home=go_to_home,
            cloudinary_available=CLOUDINARY_AVAILABLE,
            cloudinary_enabled=CLOUDINARY_ENABLED
        )
    
    elif current_page == "add_special_volume":
        show_add_special_volume(
            special_volume_service=special_volume_service,
            manga_service=manga_service,
            image_service=image_service,
            go_to_home=go_to_home
        )


if __name__ == "__main__":
    main()
