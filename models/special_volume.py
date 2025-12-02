"""
Special Volume Model: データクラス定義
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class SpecialVolume:
    """特殊巻データクラス"""
    
    id: Optional[str]  # Notion page ID
    title: str  # 特殊巻タイトル
    book_id: str  # 関連する本のID（リレーション）
    sort_order: int  # 並び順
    type: str  # 特殊巻タイプ（番外編、総集編、ガイドブック等）
    image_url: Optional[str] = None  # 画像URL
    
    @classmethod
    def from_notion_page(cls, page: Dict[str, Any]) -> 'SpecialVolume':
        """
        NotionページからSpecialVolumeオブジェクトを作成
        
        Args:
            page: Notion APIから取得したページデータ
        
        Returns:
            SpecialVolume: 特殊巻オブジェクト
        """
        props = page.get("properties", {})
        
        # タイトル
        title = ""
        if props.get("title", {}).get("title"):
            title = props["title"]["title"][0]["text"]["content"]
        
        # リレーション（book）
        book_id = ""
        if props.get("book", {}).get("relation") and props["book"]["relation"]:
            book_id = props["book"]["relation"][0]["id"]
        
        # 並び順
        sort_order = props.get("sort_order", {}).get("number", 0)
        
        # タイプ
        type_name = ""
        if props.get("type", {}).get("select"):
            type_name = props["type"]["select"]["name"]
        
        # 画像URL
        image_url = None
        if props.get("image_url", {}).get("url"):
            image_url = props["image_url"]["url"]
        
        return cls(
            id=page["id"],
            title=title,
            book_id=book_id,
            sort_order=sort_order,
            type=type_name,
            image_url=image_url
        )
    
    def to_notion_properties(self) -> Dict[str, Any]:
        """
        SpecialVolumeオブジェクトをNotion APIのプロパティ形式に変換
        
        Returns:
            Dict[str, Any]: Notion APIのプロパティ形式
        """
        properties = {
            "title": {
                "title": [{"text": {"content": self.title}}]
            },
            "book": {
                "relation": [{"id": self.book_id}] if self.book_id else []
            },
            "sort_order": {
                "number": self.sort_order
            },
            "type": {
                "select": {"name": self.type} if self.type else None
            }
        }
        
        # 画像URLがある場合のみ追加
        if self.image_url:
            properties["image_url"] = {
                "url": self.image_url
            }
        
        return properties
    
    def to_dict(self) -> Dict[str, Any]:
        """
        後方互換性のためにdict形式に変換
        
        Returns:
            Dict[str, Any]: 辞書形式のデータ
        """
        return {
            "id": self.id,
            "title": self.title,
            "book_id": self.book_id,
            "sort_order": self.sort_order,
            "type": self.type,
            "image_url": self.image_url
        }