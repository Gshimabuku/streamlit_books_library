"""
Special Volume Service: 特殊巻のCRUD操作
"""

from typing import List, Optional, Dict, Any
from collections import defaultdict
from utils.notion_client import query_notion, create_notion_page, update_notion_page, delete_notion_page
from models.special_volume import SpecialVolume


class SpecialVolumeService:
    """特殊巻のCRUD操作を提供するサービスクラス"""
    
    def __init__(self, api_key: str, database_id: str):
        """
        SpecialVolumeServiceの初期化
        
        Args:
            api_key: Notion API キー
            database_id: 特殊巻データベースID
        """
        self.api_key = api_key
        self.database_id = database_id
    
    def get_all_special_volumes(self) -> List[SpecialVolume]:
        """
        全ての特殊巻を取得（sort_order順）
        
        Returns:
            List[SpecialVolume]: 特殊巻リスト
        
        Raises:
            Exception: データベース接続エラー
        """
        try:
            # sort_orderでソートしてクエリ
            sorts = [{"property": "sort_order", "direction": "ascending"}]
            response = query_notion(self.database_id, self.api_key, sorts=sorts)
            
            special_volumes = []
            for result in response.get("results", []):
                try:
                    special_volume = SpecialVolume.from_notion_page(result)
                    special_volumes.append(special_volume)
                except Exception as e:
                    print(f"Error parsing special volume: {e}")
                    continue
            
            return special_volumes
            
        except Exception as e:
            print(f"Error fetching special volumes: {str(e)}")
            raise
    
    def get_special_volumes_by_book_id(self, book_id: str) -> List[SpecialVolume]:
        """
        指定された本IDに関連する特殊巻を取得
        
        Args:
            book_id: 本のID
        
        Returns:
            List[SpecialVolume]: 関連する特殊巻リスト
        """
        try:
            # リレーションでフィルタ
            filters = {
                "property": "book",
                "relation": {
                    "contains": book_id
                }
            }
            
            # sort_orderでソート
            sorts = [{"property": "sort_order", "direction": "ascending"}]
            
            response = query_notion(
                self.database_id, 
                self.api_key, 
                filters=filters, 
                sorts=sorts
            )
            
            special_volumes = []
            for result in response.get("results", []):
                try:
                    special_volume = SpecialVolume.from_notion_page(result)
                    special_volumes.append(special_volume)
                except Exception as e:
                    print(f"Error parsing special volume: {e}")
                    continue
            
            return special_volumes
            
        except Exception as e:
            print(f"Error fetching special volumes for book {book_id}: {str(e)}")
            return []
    
    def get_special_volume_by_id(self, special_volume_id: str) -> Optional[SpecialVolume]:
        """
        IDで特殊巻を取得
        
        Args:
            special_volume_id: 特殊巻ID
        
        Returns:
            Optional[SpecialVolume]: 特殊巻オブジェクト、見つからない場合はNone
        """
        try:
            from utils.notion_client import retrieve_notion_page
            response = retrieve_notion_page(special_volume_id, self.api_key)
            return SpecialVolume.from_notion_page(response)
        except Exception as e:
            print(f"Error fetching special volume {special_volume_id}: {str(e)}")
            return None
    
    def create_special_volume(self, special_volume: SpecialVolume) -> Optional[str]:
        """
        新しい特殊巻を作成
        
        Args:
            special_volume: 作成する特殊巻オブジェクト
        
        Returns:
            Optional[str]: 作成されたページのID、失敗時はNone
        
        Raises:
            Exception: 作成に失敗した場合
        """
        try:
            properties = special_volume.to_notion_properties()
            response = create_notion_page(self.database_id, properties, self.api_key)
            return response.get("id")
        except Exception as e:
            print(f"Error creating special volume: {str(e)}")
            raise
    
    def update_special_volume(self, special_volume: SpecialVolume) -> bool:
        """
        特殊巻を更新
        
        Args:
            special_volume: 更新する特殊巻オブジェクト
        
        Returns:
            bool: 更新成功時True、失敗時False
        """
        if not special_volume.id:
            return False
        
        try:
            properties = special_volume.to_notion_properties()
            update_notion_page(special_volume.id, properties, self.api_key)
            return True
        except Exception as e:
            print(f"Error updating special volume {special_volume.id}: {str(e)}")
            return False
    
    def delete_special_volume(self, special_volume_id: str) -> bool:
        """
        特殊巻を削除
        
        Args:
            special_volume_id: 削除する特殊巻のID
        
        Returns:
            bool: 削除成功時True、失敗時False
        """
        try:
            delete_notion_page(special_volume_id, self.api_key)
            return True
        except Exception as e:
            print(f"Error deleting special volume {special_volume_id}: {str(e)}")
            return False
    
    def group_by_book(self, special_volumes: List[SpecialVolume]) -> Dict[str, List[SpecialVolume]]:
        """
        特殊巻を本IDでグループ化
        
        Args:
            special_volumes: 特殊巻リスト
        
        Returns:
            Dict[str, List[SpecialVolume]]: {book_id: [special_volume1, ...]}
        """
        grouped = defaultdict(list)
        for special_volume in special_volumes:
            if special_volume.book_id:
                grouped[special_volume.book_id].append(special_volume)
        return dict(grouped)