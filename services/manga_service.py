"""
Manga Service: Business logic for manga CRUD operations
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from models.manga import Manga
from utils.notion_client import (
    query_notion,
    create_notion_page,
    update_notion_page,
    retrieve_notion_page,
    delete_notion_page
)


class MangaService:
    """漫画データの取得・作成・更新・削除を行うサービスクラス"""
    
    def __init__(self, api_key: str, database_id: str):
        """
        MangaServiceの初期化
        
        Args:
            api_key: Notion API Key
            database_id: Notion Database ID
        """
        self.api_key = api_key
        self.database_id = database_id
    
    def get_all_mangas(self) -> List[Manga]:
        """
        NotionDBから全ての漫画データを取得してMangaオブジェクトのリストを返す
        
        Returns:
            List[Manga]: 漫画オブジェクトのリスト（雑誌タイプ→雑誌名→かな→タイトルでソート済み）
        
        Raises:
            Exception: Notion APIでエラーが発生した場合
        """
        sorts = [
            {"property": "magazine_type", "direction": "ascending"},
            {"property": "magazine_name", "direction": "ascending"},
            {"property": "title_kana", "direction": "ascending"},
            {"property": "title", "direction": "ascending"}
        ]
        
        results = query_notion(self.database_id, self.api_key, sorts=sorts)
        
        mangas = []
        for page in results:
            try:
                # リレーション情報を解決してからMangaオブジェクトを作成
                manga = self._create_manga_with_relations(page)
                mangas.append(manga)
            except Exception as e:
                # 個別のページでエラーが発生しても続行
                print(f"Warning: Failed to parse manga page {page.get('id', 'unknown')}: {e}")
                continue
        
        return mangas
    
    def get_manga_by_id(self, page_id: str) -> Optional[Manga]:
        """
        指定されたIDの漫画データを取得
        
        Args:
            page_id: Notion Page ID
        
        Returns:
            Optional[Manga]: 漫画オブジェクト（見つからない場合はNone）
        
        Raises:
            Exception: Notion APIでエラーが発生した場合
        """
        try:
            page = retrieve_notion_page(page_id, self.api_key)
            return Manga.from_notion_page(page)
        except Exception as e:
            print(f"Error retrieving manga {page_id}: {str(e)}")
            return None
    
    def _create_manga_with_relations(self, page: dict) -> Manga:
        """
        リレーション情報を解決してMangaオブジェクトを作成
        
        Args:
            page: Notion APIから取得したページデータ
            
        Returns:
            Manga: リレーション情報を含むMangaオブジェクト
        """
        from utils.notion_client import retrieve_notion_page
        
        # 基本のMangaオブジェクトを作成
        manga = Manga.from_notion_page(page)
        
        # シリーズタイトルのリレーション情報を解決
        props = page.get("properties", {})
        series_relation = props.get("series_title", {}).get("relation", [])
        
        if series_relation:
            try:
                # 最初のリレーション先ページを取得（制限が1ページなので）
                series_page_id = series_relation[0]["id"]
                series_page = retrieve_notion_page(series_page_id, self.api_key)
                
                # リレーション先のタイトルを取得
                series_title = ""
                series_props = series_page.get("properties", {})
                if series_props.get("title", {}).get("title"):
                    series_title = series_props["title"]["title"][0]["text"]["content"]
                
                # series_titleを更新
                manga.series_title = series_title
                
            except Exception as e:
                print(f"Warning: Failed to resolve series relation for {manga.id}: {e}")
                manga.series_title = ""
        
        return manga
    
    def _find_or_create_series_page(self, series_title: str) -> Optional[str]:
        """
        シリーズタイトルで既存ページを検索、なければ新規作成
        
        Args:
            series_title: シリーズタイトル
            
        Returns:
            Optional[str]: ページID、失敗時はNone
        """
        from utils.notion_client import query_notion, create_notion_page
        
        try:
            # 既存のシリーズページを検索
            filter_condition = {
                "property": "title",
                "title": {
                    "equals": series_title
                }
            }
            
            results = query_notion(self.database_id, self.api_key, filter=filter_condition)
            
            if results:
                # 既存のページが見つかった場合
                return results[0]["id"]
            else:
                # 新規作成
                properties = {
                    "title": {"title": [{"text": {"content": series_title}}]},
                    "latest_owned_volume": {"number": 0},
                    "latest_released_volume": {"number": 0},
                    "is_completed": {"checkbox": False},
                    "series_title": {"relation": []}  # 自己参照なし
                }
                
                result = create_notion_page(self.database_id, properties, self.api_key)
                return result["id"]
                
        except Exception as e:
            print(f"Warning: Failed to find or create series page for '{series_title}': {e}")
            return None
    
    def create_manga(self, manga: Manga) -> str:
        """
        新しい漫画をNotionDBに登録
        
        Args:
            manga: 登録する漫画オブジェクト
        
        Returns:
            str: 作成されたNotion Page ID
        
        Raises:
            Exception: Notion APIでエラーが発生した場合
        """
        properties = manga.to_notion_properties()
        
        # シリーズタイトルのリレーションを設定
        if manga.series_title:
            series_page_id = self._find_or_create_series_page(manga.series_title)
            if series_page_id:
                properties["series_title"] = {"relation": [{"id": series_page_id}]}
        
        result = create_notion_page(self.database_id, properties, self.api_key)
        return result["id"]
    
    def update_manga(self, manga: Manga) -> bool:
        """
        既存の漫画情報を更新
        
        Args:
            manga: 更新する漫画オブジェクト（idフィールド必須）
        
        Returns:
            bool: 更新成功ならTrue、失敗ならFalse
        
        Raises:
            ValueError: manga.idがNoneの場合
            Exception: Notion APIでエラーが発生した場合
        """
        if not manga.id:
            raise ValueError("Manga ID is required for update operation")
        
        properties = manga.to_notion_properties()
        
        # シリーズタイトルのリレーションを設定
        if manga.series_title:
            series_page_id = self._find_or_create_series_page(manga.series_title)
            if series_page_id:
                properties["series_title"] = {"relation": [{"id": series_page_id}]}
        
        try:
            update_notion_page(manga.id, properties, self.api_key)
            return True
        except Exception as e:
            print(f"Error updating manga {manga.id}: {str(e)}")
            return False
    
    def delete_manga(self, page_id: str) -> bool:
        """
        指定されたIDの漫画を削除
        
        Args:
            page_id: 削除するNotion Page ID
        
        Returns:
            bool: 削除成功ならTrue、失敗ならFalse
        """
        try:
            delete_notion_page(page_id, self.api_key)
            return True
        except Exception as e:
            print(f"Error deleting manga {page_id}: {str(e)}")
            return False
    
    @staticmethod
    def group_by_magazine(mangas: List[Manga]) -> Dict[str, Dict[str, List[Manga]]]:
        """
        漫画リストを雑誌タイプ→雑誌名でグループ化
        
        Args:
            mangas: 漫画オブジェクトのリスト
        
        Returns:
            Dict[str, Dict[str, List[Manga]]]: {magazine_type: {magazine_name: [manga1, manga2, ...]}}
        """
        grouped = defaultdict(lambda: defaultdict(list))
        
        for manga in mangas:
            magazine_type = manga.magazine_type or "その他"
            magazine_name = manga.magazine_name or "不明"
            grouped[magazine_type][magazine_name].append(manga)
        
        return grouped
    
    @staticmethod
    def sort_magazine_names(
        magazine_names: List[str],
        magazine_type: str
    ) -> List[str]:
        """
        雑誌名をカスタム順序でソート
        
        Args:
            magazine_names: ソートする雑誌名のリスト
            magazine_type: 雑誌タイプ（ジャンプ、マガジン、サンデー、その他）
        
        Returns:
            List[str]: ソート済みの雑誌名リスト
        """
        # 雑誌タイプごとの表示順序定義
        magazine_name_order = {
            "ジャンプ": ["週刊少年ジャンプ", "週刊ヤングジャンプ", "ジャンプ+", "ジャンプSQ", "ジャンプGIGA"],
            "マガジン": ["週刊少年マガジン", "週刊ヤングマガジン", "月刊少年マガジン", "別冊少年マガジン"],
            "サンデー": ["週刊少年サンデー", "少年サンデーＳ（スーパー）", "裏サンデー"],
            "その他": ["週刊ビッグコミックスピリッツ", "月刊コミックゼノン", "月刊アフタヌーン"]
        }
        
        defined_order = magazine_name_order.get(magazine_type, [])
        
        # 定義済みの順序に従って並び替え
        sorted_names = []
        for name in defined_order:
            if name in magazine_names:
                sorted_names.append(name)
        
        # 定義されていない雑誌名は辞書順で末尾に追加
        remaining_names = [name for name in magazine_names if name not in defined_order]
        sorted_names.extend(sorted(remaining_names))
        
        return sorted_names
