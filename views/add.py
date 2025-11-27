"""
Add Page: New manga registration form
"""

import streamlit as st
import datetime
from utils.config import Config
from utils.kana_converter import title_to_kana
from utils.notion_client import create_notion_page
from services.manga_service import MangaService
from services.image_service import ImageService
from components.book_form import BookFormFields
from models.manga import Manga


def show_add_book(
    manga_service: MangaService,
    image_service: ImageService,
    go_to_home: callable,
    notion_api_key: str,
    books_database_id: str,
    cloudinary_available: bool,
    cloudinary_enabled: bool
):
    """新規漫画登録画面"""
    st.header("➕ 新しい漫画を登録")
    
    # 戻るボタン
    if st.button("← ホームに戻る"):
        go_to_home()
        st.rerun()
    
    with st.form("add_book_form"):
        # BookFormFieldsコンポーネントを使用
        basic_info = BookFormFields.render_basic_info()
        title = basic_info["title"]
        title_kana = basic_info["title_kana"]
        magazine_type = basic_info["magazine_type"]
        magazine_name = basic_info["magazine_name"]
        
        # シリーズ情報を取得（新規作成時は親作品のみ選択可能）
        try:
            all_mangas = manga_service.get_all_mangas()
        except Exception:
            all_mangas = []
        
        series_info = BookFormFields.render_series_selection(
            all_mangas=all_mangas,
            current_manga_id=None  # 新規作成時はNone
        )
        parent_id = series_info["parent_id"]
        children_ids = []  # 新規作成時は子作品なし
        
        volume_info = BookFormFields.render_volume_info()
        latest_owned_volume = volume_info["latest_owned_volume"]
        latest_released_volume = volume_info["latest_released_volume"]
        
        uploaded_file = BookFormFields.render_image_info()
        
        # Cloudinaryが利用可能かチェック（プレビュー後のメッセージ）
        if uploaded_file is not None:
            if cloudinary_enabled and cloudinary_available:
                st.info("📤 登録時にCloudinaryにアップロードされます")
            else:
                st.warning("⚠️ Cloudinary設定が見つかりません。画像URLは保存されません。")
        
        is_completed = BookFormFields.render_completion_status()
        
        latest_release_date, use_next_release_date, next_release_date = BookFormFields.render_date_info()
        
        detail_info = BookFormFields.render_detail_info()
        missing_volumes = detail_info["missing_volumes"]
        special_volumes = detail_info["special_volumes"]
        owned_media = detail_info["owned_media"]
        notes = detail_info["notes"]
        
        # 登録ボタン
        submitted = st.form_submit_button("📚 漫画を登録", type="primary")
        
        if submitted:
            if not title or not magazine_type:
                st.error("❌ タイトルと連載誌タイプは必須項目です")
            elif latest_owned_volume > latest_released_volume:
                st.error("❌ 所持巻数が発売済み最新巻を超えています")
            else:
                try:
                    # ImageServiceを使用して画像アップロード
                    final_image_url = None
                    
                    if uploaded_file is not None and image_service.is_available():
                        with st.spinner("画像をアップロード中..."):
                            final_image_url = image_service.upload_image(uploaded_file)
                            st.success(f"✅ 画像アップロード完了: {uploaded_file.name}")
                    elif uploaded_file is not None:
                        st.warning("⚠️ Cloudinary設定がないため、画像はアップロードされませんでした")
                    
                    # タイトルかなを自動生成（未入力の場合）
                    final_title_kana = title_kana.strip() if title_kana else ""
                    ai_generated = False
                    
                    if not final_title_kana and title:
                        openai_api_key = Config.get_openai_api_key()
                        use_ai = openai_api_key is not None
                        ai_generated = use_ai
                        
                        with st.spinner("タイトルかなを生成中..." + (" (AI使用)" if use_ai else "")):
                            final_title_kana = title_to_kana(title, use_ai=use_ai, api_key=openai_api_key)
                    
                    # Mangaオブジェクトを作成
                    # リレーション情報の準備（新規作成時は親作品のみ）
                    related_books_to = [parent_id] if parent_id else None
                    related_books_from = None  # 新規作成時は子作品なし
                    
                    new_manga = Manga(
                        id="",  # 作成時は空文字
                        title=title,
                        title_kana=final_title_kana,
                        magazine_type=magazine_type,
                        magazine_name=magazine_name,
                        latest_owned_volume=latest_owned_volume,
                        latest_released_volume=latest_released_volume,
                        is_completed=is_completed,
                        image_url=final_image_url,
                        related_books_to=related_books_to,
                        related_books_from=related_books_from,
                        latest_release_date=latest_release_date,
                        next_release_date=next_release_date if use_next_release_date else None,
                        missing_volumes=missing_volumes,
                        special_volumes=special_volumes,
                        owned_media=owned_media,
                        notes=notes
                    )
                    
                    # MangaServiceを使用して登録
                    try:
                        with st.spinner("Notionに登録中..."):
                            result_id = manga_service.create_manga(new_manga)
                            
                            # リレーション設定後の相互更新処理（親作品の場合のみ）
                            if parent_id:
                                with st.spinner("シリーズ関係を更新中..."):
                                    manga_service.update_parent_relation(
                                        manga_id=result_id,
                                        old_parent_id=None,
                                        new_parent_id=parent_id
                                    )
                        
                        st.success("✅ 漫画が正常に登録されました！")
                        st.balloons()
                        
                        # 画像URLがある場合は表示
                        if final_image_url:
                            st.markdown(f"🔗 [画像を開く]({final_image_url})")
                        
                        # かなが自動生成された場合は通知（AI生成の場合は明示）
                        if not title_kana.strip() and final_title_kana:
                            if ai_generated:
                                st.info(f"🤖 タイトルかなをAIで生成しました: **{final_title_kana}** (AI生成)")
                            else:
                                st.info(f"💡 タイトルかなを自動生成しました: {final_title_kana}")
                        
                        # セッション状態で登録成功をマーク
                        st.session_state.registration_success = True
                        
                    except Exception as full_error:
                        st.error(f"❌ 登録に失敗しました: {str(full_error)}")
                        
                        # 最小限のプロパティで再試行
                        st.warning("🔄 基本プロパティのみで再試行します...")
                        
                        minimal_properties = {
                            "title": {"title": [{"text": {"content": title}}]},
                            "latest_owned_volume": {"number": latest_owned_volume},
                            "latest_released_volume": {"number": latest_released_volume},
                            "is_completed": {"checkbox": is_completed},
                            "latest_release_date": {"date": {"start": latest_release_date.isoformat()}}
                        }
                        
                        try:
                            with st.spinner("基本プロパティで登録中..."):
                                result = create_notion_page(books_database_id, minimal_properties, notion_api_key)
                            
                            st.success("✅ 基本プロパティで登録成功！")
                            st.info("💡 基本情報のみ保存されました。詳細情報は後で編集してください。")
                            
                            # セッション状態で登録成功をマーク
                            st.session_state.registration_success = True
                            
                        except Exception as minimal_error:
                            st.error(f"❌ 基本プロパティでも登録失敗: {str(minimal_error)}")
                            st.info("💡 Notionデータベースのプロパティ設定を確認してください。")
                    
                except Exception as e:
                    st.error(f"❌ 登録処理でエラーが発生しました: {str(e)}")
    
    # フォーム外で登録成功状態をチェック
    if st.session_state.get("registration_success", False):
        st.success("🎉 登録が完了しました！")
        if st.button("📚 ホームに戻る", type="primary"):
            st.session_state.registration_success = False
            go_to_home()
            st.rerun()
