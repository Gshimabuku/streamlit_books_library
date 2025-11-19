"""
Image Service: Cloudinary image upload and deletion operations
"""

import re
from typing import Optional, Any


class ImageService:
    """Cloudinary画像のアップロード・削除を行うサービスクラス"""
    
    def __init__(self, cloudinary_available: bool = False, cloudinary_enabled: bool = False):
        """
        ImageServiceの初期化
        
        Args:
            cloudinary_available: Cloudinaryライブラリがインポート可能か
            cloudinary_enabled: Cloudinary設定が有効か
        """
        self.cloudinary_available = cloudinary_available
        self.cloudinary_enabled = cloudinary_enabled
        
        if self.cloudinary_available and self.cloudinary_enabled:
            try:
                import cloudinary.uploader
                self.uploader = cloudinary.uploader
            except ImportError:
                self.cloudinary_available = False
                self.cloudinary_enabled = False
                self.uploader = None
        else:
            self.uploader = None
    
    def is_available(self) -> bool:
        """
        Cloudinaryサービスが利用可能かチェック
        
        Returns:
            bool: 利用可能ならTrue
        """
        return self.cloudinary_available and self.cloudinary_enabled and self.uploader is not None
    
    def upload_image(self, file: Any) -> Optional[str]:
        """
        画像をCloudinaryにアップロード
        
        Args:
            file: アップロードするファイルオブジェクト（Streamlit UploadedFile等）
        
        Returns:
            Optional[str]: アップロード成功時はsecure_url、失敗時はNone
        
        Raises:
            Exception: アップロードに失敗した場合
        """
        if not self.is_available():
            raise Exception("Cloudinary is not available or not properly configured")
        
        try:
            result = self.uploader.upload(file)
            return result.get("secure_url")
        except Exception as e:
            print(f"Error uploading image: {str(e)}")
            raise
    
    def delete_image(self, image_url: str) -> bool:
        """
        CloudinaryのURLから画像を削除
        
        Args:
            image_url: Cloudinary画像のURL
        
        Returns:
            bool: 削除成功ならTrue、失敗ならFalse
        """
        if not self.is_available():
            print("Cloudinary is not available")
            return False
        
        if not image_url or "cloudinary.com" not in image_url:
            print(f"Invalid Cloudinary URL: {image_url}")
            return False
        
        try:
            public_id = self._extract_public_id(image_url)
            if not public_id:
                print(f"Could not extract public_id from URL: {image_url}")
                return False
            
            result = self.uploader.destroy(public_id)
            
            # Cloudinaryのレスポンスは {"result": "ok"} または {"result": "not found"}
            return result.get("result") == "ok"
            
        except Exception as e:
            print(f"Error deleting image: {str(e)}")
            return False
    
    @staticmethod
    def _extract_public_id(image_url: str) -> Optional[str]:
        """
        CloudinaryのURLからpublic_idを抽出
        
        Args:
            image_url: Cloudinary画像のURL
                例: https://res.cloudinary.com/demo/image/upload/v1234567890/sample.jpg
                例: https://res.cloudinary.com/demo/image/upload/sample.jpg
        
        Returns:
            Optional[str]: public_id（例: "sample"）、抽出失敗時はNone
        """
        # URLパターン: /upload/[v数字/]ファイル名[.拡張子]
        # public_idはファイル名部分（拡張子なし）
        match = re.search(r'/upload/(?:v\d+/)?([^/]+?)(?:\.[^.]+)?$', image_url)
        
        if match:
            return match.group(1)
        
        return None
    
    def replace_image(self, old_url: Optional[str], new_file: Any) -> Optional[str]:
        """
        画像を置き換え（古い画像を削除して新しい画像をアップロード）
        
        Args:
            old_url: 削除する古い画像のURL（Noneの場合は削除スキップ）
            new_file: アップロードする新しいファイル
        
        Returns:
            Optional[str]: 新しい画像のURL、失敗時はNone
        
        Raises:
            Exception: アップロードに失敗した場合
        """
        # 新しい画像をアップロード
        new_url = self.upload_image(new_file)
        
        # アップロード成功後、古い画像を削除
        if new_url and old_url:
            self.delete_image(old_url)  # 削除失敗は無視
        
        return new_url
