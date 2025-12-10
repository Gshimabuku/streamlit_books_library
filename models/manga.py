"""漫画データモデル"""
from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

@dataclass
class Manga:
    """漫画データクラス
    
    Notionデータベースのプロパティをアプリケーション内で扱いやすい形に変換
    """
    id: str
    title: str
    title_kana: str
    magazine_type: str
    magazine_name: str
    latest_owned_volume: int
    latest_released_volume: int
    is_completed: bool
    image_url: Optional[str] = None
    related_books_to: Optional[list] = None  # booksとのリレーション
    related_books_from: Optional[list] = None  # booksからのリレーション
    latest_release_date: Optional[date] = None
    next_release_date: Optional[date] = None
    missing_volumes: str = ""
    special_volumes: str = ""
    owned_media: str = "単行本"
    notes: str = ""
    
    # Notion APIの生データも保持（互換性のため）
    _page_data: Optional[dict] = None
    
    @property
    def actual_owned_volume(self) -> int:
        """実際の所持巻数（抜け巻を除く）
        
        Returns:
            int: 抜け巻を引いた実際の所持巻数
        """
        if not self.missing_volumes:
            return self.latest_owned_volume
        
        try:
            missing_list = [v.strip() for v in self.missing_volumes.split(",") if v.strip()]
            return self.latest_owned_volume - len(missing_list)
        except:
            return self.latest_owned_volume
    
    @property
    def has_unpurchased(self) -> bool:
        """未購入巻があるか
        
        Returns:
            bool: 実所持巻数が発売済み巻数より少ない場合True
        """
        return self.actual_owned_volume < self.latest_released_volume
    
    @property
    def completion_status(self) -> str:
        """完結状態のラベル
        
        Returns:
            str: "完結" または "連載中"
        """
        return "完結" if self.is_completed else "連載中"
    
    def to_dict(self) -> dict:
        """辞書形式に変換（後方互換性のため）
        
        Returns:
            dict: 従来のbook_data形式
        """
        return {
            "id": self.id,
            "title": self.title,
            "image_url": self.image_url,
            "latest_owned_volume": self.latest_owned_volume,
            "latest_released_volume": self.latest_released_volume,
            "is_completed": self.is_completed,
            "magazine_type": self.magazine_type,
            "magazine_name": self.magazine_name,
            "page_data": self._page_data
        }
    
    @classmethod
    def from_notion_page(cls, page: dict) -> "Manga":
        """NotionページからMangaオブジェクトを生成
        
        Args:
            page: Notion APIから取得したページデータ
            
        Returns:
            Manga: 変換されたMangaオブジェクト
        """
        props = page["properties"]
        
        # タイトル取得
        title = "タイトル不明"
        if props.get("title", {}).get("title"):
            title = props["title"]["title"][0]["text"]["content"]
        
        # タイトルかな
        title_kana = ""
        if props.get("title_kana", {}).get("rich_text") and props["title_kana"]["rich_text"]:
            title_kana = props["title_kana"]["rich_text"][0]["text"]["content"]
        
        # リレーション情報の取得（新しいプロパティ名を使用）
        related_books_to = None
        if props.get("relation_books_to", {}).get("relation"):
            related_books_to = [rel["id"] for rel in props["relation_books_to"]["relation"]]
        
        related_books_from = None
        if props.get("relation_books_from", {}).get("relation"):
            related_books_from = [rel["id"] for rel in props["relation_books_from"]["relation"]]
        
        # 画像URL
        image_url = props.get("image_url", {}).get("url")
        if not image_url or not image_url.startswith(('http://', 'https://')):
            image_url = None
        
        # 雑誌タイプ
        magazine_type = "その他"
        if props.get("magazine_type", {}).get("select"):
            magazine_type = props["magazine_type"]["select"]["name"]
        
        # 雑誌名
        magazine_name = "不明"
        if props.get("magazine_name", {}).get("rich_text") and props["magazine_name"]["rich_text"]:
            magazine_name = props["magazine_name"]["rich_text"][0]["text"]["content"]
        
        # 日付情報
        latest_release_date = None
        if props.get("latest_release_date", {}).get("date"):
            try:
                date_str = props["latest_release_date"]["date"]["start"]
                latest_release_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                pass
        
        next_release_date = None
        if props.get("next_release_date", {}).get("date"):
            try:
                date_str = props["next_release_date"]["date"]["start"]
                next_release_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                pass
        
        # その他のテキストフィールド
        missing_volumes = ""
        if props.get("missing_volumes", {}).get("rich_text") and props["missing_volumes"]["rich_text"]:
            missing_volumes = props["missing_volumes"]["rich_text"][0]["text"]["content"]
        
        special_volumes = ""
        if props.get("special_volumes", {}).get("rich_text") and props["special_volumes"]["rich_text"]:
            special_volumes = props["special_volumes"]["rich_text"][0]["text"]["content"]
        
        owned_media = "単行本"
        if props.get("owned_media", {}).get("select"):
            owned_media = props["owned_media"]["select"]["name"]
        
        notes = ""
        if props.get("notes", {}).get("rich_text") and props["notes"]["rich_text"]:
            notes = props["notes"]["rich_text"][0]["text"]["content"]
        
        return cls(
            id=page["id"],
            title=title,
            title_kana=title_kana,
            magazine_type=magazine_type,
            magazine_name=magazine_name,
            latest_owned_volume=props.get("latest_owned_volume", {}).get("number", 0),
            latest_released_volume=props.get("latest_released_volume", {}).get("number", 0),
            is_completed=props.get("is_completed", {}).get("checkbox", False),
            image_url=image_url,
            related_books_to=related_books_to,
            related_books_from=related_books_from,
            latest_release_date=latest_release_date,
            next_release_date=next_release_date,
            missing_volumes=missing_volumes,
            special_volumes=special_volumes,
            owned_media=owned_media,
            notes=notes,
            _page_data=page  # 元データを保持
        )
    
    def to_notion_properties(self) -> dict:
        """Notionプロパティ形式に変換
        
        Returns:
            dict: Notion API用のプロパティ辞書
        """
        try:
            # 基本プロパティ（必須）
            properties = {
                "title": {"title": [{"text": {"content": str(self.title) if self.title else ""}}]},
                "latest_owned_volume": {"number": int(self.latest_owned_volume) if self.latest_owned_volume is not None else 0},
                "latest_released_volume": {"number": int(self.latest_released_volume) if self.latest_released_volume is not None else 0},
                "is_completed": {"checkbox": bool(self.is_completed)}
            }
            
            # オプショナルプロパティ
            if self.title_kana and str(self.title_kana).strip():
                properties["title_kana"] = {"rich_text": [{"text": {"content": str(self.title_kana)}}]}
            
            # リレーション情報を設定（新しいプロパティ名を使用）
            if self.related_books_to and isinstance(self.related_books_to, list):
                valid_ids = [book_id for book_id in self.related_books_to if book_id and isinstance(book_id, str)]
                if valid_ids:
                    properties["relation_books_to"] = {"relation": [{"id": book_id} for book_id in valid_ids]}
            
            if self.related_books_from and isinstance(self.related_books_from, list):
                valid_ids = [book_id for book_id in self.related_books_from if book_id and isinstance(book_id, str)]
                if valid_ids:
                    properties["relation_books_from"] = {"relation": [{"id": book_id} for book_id in valid_ids]}
        
            # 日付フィールド
            if self.latest_release_date:
                try:
                    properties["latest_release_date"] = {"date": {"start": self.latest_release_date.isoformat()}}
                except:
                    pass  # 日付変換に失敗した場合は無視
            
            if self.next_release_date:
                try:
                    properties["next_release_date"] = {"date": {"start": self.next_release_date.isoformat()}}
                except:
                    pass  # 日付変換に失敗した場合は無視
            
            # セレクトフィールド
            if self.magazine_type and str(self.magazine_type).strip():
                properties["magazine_type"] = {"select": {"name": str(self.magazine_type)}}
            
            # リッチテキストフィールド
            if self.magazine_name and str(self.magazine_name).strip():
                properties["magazine_name"] = {"rich_text": [{"text": {"content": str(self.magazine_name)}}]}
            else:
                properties["magazine_name"] = {"rich_text": []}
            
            if self.missing_volumes and str(self.missing_volumes).strip():
                properties["missing_volumes"] = {"rich_text": [{"text": {"content": str(self.missing_volumes)}}]}
            else:
                properties["missing_volumes"] = {"rich_text": []}
            
            if self.special_volumes and str(self.special_volumes).strip():
                properties["special_volumes"] = {"rich_text": [{"text": {"content": str(self.special_volumes)}}]}
            else:
                properties["special_volumes"] = {"rich_text": []}
            
            if self.owned_media and str(self.owned_media).strip():
                properties["owned_media"] = {"select": {"name": str(self.owned_media)}}
            
            if self.notes and str(self.notes).strip():
                properties["notes"] = {"rich_text": [{"text": {"content": str(self.notes)}}]}
            else:
                properties["notes"] = {"rich_text": []}
            
            # URLフィールド
            if self.image_url and str(self.image_url).strip() and str(self.image_url).startswith(('http://', 'https://')):
                properties["image_url"] = {"url": str(self.image_url)}
            
            return properties
        
        except Exception as e:
            print(f"Error in to_notion_properties: {str(e)}")
            print(f"Manga data: title={self.title}, id={self.id}")
            raise
    
    def calculate_actual_owned_count(self) -> int:
        """実際の所持冊数を計算（所持最新巻から抜け巻を引いた数）
        
        Returns:
            int: 実際に所持している冊数
        """
        owned_count = self.latest_owned_volume
        
        # 抜け巻がある場合の計算
        if self.missing_volumes:
            try:
                missing_list = [vol.strip() for vol in self.missing_volumes.split(",") if vol.strip()]
                missing_count = len(missing_list)
                return max(0, owned_count - missing_count)
            except:
                return owned_count
        
        return owned_count
    
    def calculate_total_owned_count_with_specials(self, special_volumes_count: int = 0) -> int:
        """特殊巻を含む合計所持冊数を計算
        
        Args:
            special_volumes_count: 特殊巻の冊数
        
        Returns:
            int: 通常巻 + 特殊巻の合計冊数
        """
        return self.calculate_actual_owned_count() + special_volumes_count
