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
        全ての漫画データを取得
        
        Returns:
            List[Manga]: 漫画オブジェクトのリスト
            
        Raises:
            Exception: Notion APIでエラーが発生した場合
        """
        results = query_notion(self.database_id, self.api_key)
        
        mangas = []
        for page in results:
            try:
                manga = Manga.from_notion_page(page)
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
            from utils.notion_client import retrieve_notion_page
            page = retrieve_notion_page(page_id, self.api_key)
            return Manga.from_notion_page(page)
        except Exception as e:
            print(f"Error retrieving manga {page_id}: {str(e)}")
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
    
    def update_parent_relation(
        self,
        manga_id: str,
        old_parent_id: str = None,
        new_parent_id: str = None
    ) -> None:
        """
        親作品との関係を更新（簡易版）
        
        Args:
            manga_id: 対象の漫画ID
            old_parent_id: 変更前の親作品ID
            new_parent_id: 変更後の親作品ID
        """
        # 古い親から自分を削除
        if old_parent_id:
            try:
                old_parent = self.get_manga_by_id(old_parent_id)
                if old_parent and old_parent.related_books_from:
                    if manga_id in old_parent.related_books_from:
                        old_parent.related_books_from.remove(manga_id)
                        if not old_parent.related_books_from:
                            old_parent.related_books_from = None
                        self.update_manga(old_parent)
            except Exception as e:
                print(f"Warning: Failed to remove from old parent {old_parent_id}: {e}")
        
        # 新しい親に自分を追加
        if new_parent_id:
            try:
                new_parent = self.get_manga_by_id(new_parent_id)
                if new_parent:
                    if new_parent.related_books_from is None:
                        new_parent.related_books_from = []
                    if manga_id not in new_parent.related_books_from:
                        new_parent.related_books_from.append(manga_id)
                        self.update_manga(new_parent)
            except Exception as e:
                print(f"Warning: Failed to add to new parent {new_parent_id}: {e}")
    
    def update_series_relations(
        self, 
        created_manga_id: str, 
        parent_id: str = None, 
        children_ids: list = None
    ) -> None:
        """
        作成された漫画のシリーズ関係を双方向で更新
        
        Args:
            created_manga_id: 作成された漫画のID
            parent_id: 親作品のID
            children_ids: 子作品のIDリスト
        """
        # 親作品がある場合、親のrelated_books_fromに新しい作品を追加
        if parent_id:
            try:
                parent_manga = self.get_manga_by_id(parent_id)
                if parent_manga:
                    if parent_manga.related_books_from is None:
                        parent_manga.related_books_from = []
                    
                    if created_manga_id not in parent_manga.related_books_from:
                        parent_manga.related_books_from.append(created_manga_id)
                        self.update_manga(parent_manga)
            except Exception as e:
                print(f"Warning: Failed to update parent relation for {parent_id}: {e}")
        
        # 子作品がある場合、各子のrelated_books_toに新しい作品を設定
        if children_ids:
            for child_id in children_ids:
                try:
                    child_manga = self.get_manga_by_id(child_id)
                    if child_manga:
                        # 子は一つの親しか持てないので、リストを置き換え
                        child_manga.related_books_to = [created_manga_id]
                        self.update_manga(child_manga)
                except Exception as e:
                    print(f"Warning: Failed to update child relation for {child_id}: {e}")
    
    def get_series_info(self, manga: Manga) -> Dict[str, Any]:
        """
        指定された漫画のシリーズ情報を取得
        
        Args:
            manga: 対象の漫画オブジェクト
            
        Returns:
            Dict[str, Any]: {
                "parent": Manga|None, 
                "children": List[Manga],
                "is_series_root": bool
            }
        """
        parent = None
        children = []
        
        # 親作品を取得
        if manga.related_books_to:
            try:
                parent_id = manga.related_books_to[0]  # 親は一つだけ
                parent = self.get_manga_by_id(parent_id)
            except Exception as e:
                print(f"Warning: Failed to get parent for {manga.id}: {e}")
        
        # 子作品を取得
        if manga.related_books_from:
            for child_id in manga.related_books_from:
                try:
                    child = self.get_manga_by_id(child_id)
                    if child:
                        children.append(child)
                except Exception as e:
                    print(f"Warning: Failed to get child {child_id} for {manga.id}: {e}")
        
        is_series_root = parent is None and len(children) > 0
        
        return {
            "parent": parent,
            "children": children,
            "is_series_root": is_series_root
        }
    
    def update_changed_relations(
        self,
        manga_id: str,
        old_parent_id: str = None,
        new_parent_id: str = None,
        old_children_ids: list = None,
        new_children_ids: list = None
    ) -> None:
        """
        編集時のリレーション変更を双方向で更新
        
        Args:
            manga_id: 編集対象の漫画ID
            old_parent_id: 変更前の親作品ID
            new_parent_id: 変更後の親作品ID
            old_children_ids: 変更前の子作品IDリスト
            new_children_ids: 変更後の子作品IDリスト
        """
        if old_children_ids is None:
            old_children_ids = []
        if new_children_ids is None:
            new_children_ids = []
        
        # 親の関係変更処理
        if old_parent_id != new_parent_id:
            # 古い親から自分を削除
            if old_parent_id:
                try:
                    old_parent = self.get_manga_by_id(old_parent_id)
                    if old_parent and old_parent.related_books_from:
                        if manga_id in old_parent.related_books_from:
                            old_parent.related_books_from.remove(manga_id)
                            self.update_manga(old_parent)
                except Exception as e:
                    print(f"Warning: Failed to remove from old parent {old_parent_id}: {e}")
            
            # 新しい親に自分を追加
            if new_parent_id:
                try:
                    new_parent = self.get_manga_by_id(new_parent_id)
                    if new_parent:
                        if new_parent.related_books_from is None:
                            new_parent.related_books_from = []
                        if manga_id not in new_parent.related_books_from:
                            new_parent.related_books_from.append(manga_id)
                            self.update_manga(new_parent)
                except Exception as e:
                    print(f"Warning: Failed to add to new parent {new_parent_id}: {e}")
        
        # 子の関係変更処理
        old_children_set = set(old_children_ids)
        new_children_set = set(new_children_ids)
        
        # 削除された子から自分を削除
        removed_children = old_children_set - new_children_set
        for child_id in removed_children:
            try:
                child = self.get_manga_by_id(child_id)
                if child and child.related_books_to:
                    if manga_id in child.related_books_to:
                        child.related_books_to.remove(manga_id)
                        # 子の親がなくなる場合は None にする
                        if not child.related_books_to:
                            child.related_books_to = None
                        self.update_manga(child)
            except Exception as e:
                print(f"Warning: Failed to remove from child {child_id}: {e}")
        
        # 追加された子に自分を設定
        added_children = new_children_set - old_children_set
        for child_id in added_children:
            try:
                child = self.get_manga_by_id(child_id)
                if child:
                    # 子は一つの親しか持てないので、リストを置き換え
                    child.related_books_to = [manga_id]
                    self.update_manga(child)
            except Exception as e:
                print(f"Warning: Failed to add to child {child_id}: {e}")
