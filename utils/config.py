"""アプリケーション設定管理"""
import streamlit as st
import os

class Config:
    """設定クラス - Notion/Cloudinary/OpenAIの設定を管理"""
    
    @staticmethod
    def load_notion_config():
        """Notion設定を読み込み
        
        Returns:
            dict: api_key と 2つのdatabase_id を含む辞書
            
        Raises:
            SystemExit: 設定が見つからない場合
        """
        try:
            return {
                "api_key": st.secrets["notion"]["api_key"],
                "books_database_id": st.secrets["notion"]["books_database_id"],
                "special_volumes_database_id": st.secrets["notion"]["special_volumes_database_id"]
            }
        except Exception as e:
            st.error(f"🔧 **Notion設定エラー**: {str(e)}")
            st.markdown("""
            ### 📋 secrets.toml ファイルを確認してください
            
            `.streamlit/secrets.toml` ファイルに以下の形式で設定が必要です：
            
            ```toml
            [notion]
            api_key = "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
            books_database_id = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
            special_volumes_database_id = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
            ```
            """)
            st.stop()
    
    @staticmethod
    def load_cloudinary_config():
        """Cloudinary設定を読み込み
        
        Returns:
            dict or None: 設定が存在する場合は辞書、ない場合はNone
        """
        try:
            return {
                "cloud_name": st.secrets["cloudinary"]["cloud_name"],
                "api_key": st.secrets["cloudinary"]["api_key"],
                "api_secret": st.secrets["cloudinary"]["api_secret"]
            }
        except:
            return None
    
    @staticmethod
    def get_openai_api_key():
        """OpenAI APIキーを取得
        
        Returns:
            str or None: APIキーまたはNone
        """
        try:
            return st.secrets.get("openai", {}).get("api_key") or os.environ.get("OPENAI_API_KEY")
        except:
            return None
    
    @staticmethod
    def check_cloudinary_available():
        """Cloudinaryライブラリが利用可能かチェック
        
        Returns:
            bool: 利用可能な場合True
        """
        try:
            import cloudinary
            return True
        except ImportError:
            return False
