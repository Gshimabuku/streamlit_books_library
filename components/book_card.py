"""
BookCard Component: 漫画カード表示用コンポーネント
"""

from typing import Optional
from models.manga import Manga
from config.constants import DEFAULT_IMAGE_URL


class BookCard:
    """漫画カードのHTML生成を担当するコンポーネント"""
    
    @staticmethod
    def render(manga: Manga) -> str:
        """
        Mangaオブジェクトから漫画カードのHTMLを生成
        
        Args:
            manga: 表示する漫画オブジェクト
        
        Returns:
            str: カード表示用のHTML文字列
        """
        # 画像HTMLを準備
        image_html = BookCard._get_image_html(manga.image_url, manga.title)
        
        # 完結状態と未購入バッジ
        completion_status = manga.completion_status
        is_completed = manga.is_completed
        has_unpurchased = manga.has_unpurchased
        unpurchased_badge = '<span class="unpurchased-badge">未購入あり</span>' if has_unpurchased else ""
        
        # 実所持巻数と発売済み巻数
        actual_owned = manga.actual_owned_volume
        released = manga.latest_released_volume
        
        # 連載誌情報
        magazine_info = ""
        if manga.magazine_name:
            magazine_info = f'<div class="book-magazine-info">📰 {manga.magazine_name}</div>'
        
        # 巻数情報
        volume_info = f'<div class="book-volume-info">📖 {actual_owned}/{released}巻</div>'

        # 所持媒体情報
        media_info = ""
        if manga.owned_media:
            media_info = f'<div class="book-media-info">💻 {manga.owned_media}</div>'
        
        # HTMLテンプレート
        card_html = f"""
        <div class="book-card">
            <div class="mobile-book-image">
                {image_html}
            </div>
            <div class="mobile-book-info">
                <div class="status-container">
                    <span class="status-badge {'status-completed' if is_completed else 'status-ongoing'}">{completion_status}</span>{unpurchased_badge}
                </div>
                <h3>{manga.title}</h3>
                {magazine_info}
                {volume_info}
                {media_info}
            </div>
        </div>
        """
        
        return card_html
    
    @staticmethod
    def _get_image_html(image_url: Optional[str], title: str) -> str:
        """
        画像URLから画像HTMLを生成（エラーハンドリング付き）
        
        Args:
            image_url: 画像URL（Noneの場合はデフォルト画像）
            title: 画像のalt属性用タイトル
        
        Returns:
            str: 画像表示用のHTML文字列
        """
        try:
            if image_url and image_url != "":
                return f'<img src="{image_url}" alt="{title}">'
            else:
                return f'<img src="{DEFAULT_IMAGE_URL}" alt="画像なし">'
        except Exception:
            return f'<img src="{DEFAULT_IMAGE_URL}" alt="画像読み込みエラー">'
    
    @staticmethod
    def render_magazine_header(magazine_name: str) -> str:
        """
        雑誌名ヘッダーのHTMLを生成
        
        Args:
            magazine_name: 雑誌名
        
        Returns:
            str: 雑誌名ヘッダーのHTML
        """
        return f'<div class="magazine-name-header">📖 {magazine_name}</div>'
