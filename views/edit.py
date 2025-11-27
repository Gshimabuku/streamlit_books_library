"""
Edit Page: Manga information edit form
"""

import streamlit as st
import datetime
from utils.config import Config
from utils.kana_converter import title_to_kana
from services.manga_service import MangaService
from services.image_service import ImageService
from components.book_form import BookFormFields
from models.manga import Manga


def show_edit_book(
    manga_service: MangaService,
    image_service: ImageService,
    go_to_home: callable,
    cloudinary_available: bool,
    cloudinary_enabled: bool
):
    """漫画編集画面"""
    st.header("✏️ 漫画情報を編集")
    
    # 戻るボタン
    if st.button("← 詳細に戻る"):
        st.session_state.page = "book_detail"
        st.rerun()
    
    if st.session_state.selected_book is None:
        st.error("編集する漫画が選択されていません")
        return
    
    book = st.session_state.selected_book
    page_data = book.get("page_data", {})
    props = page_data.get("properties", {})
    
    # 既存データを取得
    current_title = book.get("title", "")
    current_magazine_type = book.get("magazine_type", "その他")
    
    # 雑誌名
    current_magazine_name = ""
    if props.get("magazine_name", {}).get("rich_text") and props["magazine_name"]["rich_text"]:
        current_magazine_name = props["magazine_name"]["rich_text"][0]["text"]["content"]
    
    # タイトルかな
    current_title_kana = ""
    if props.get("title_kana", {}).get("rich_text") and props["title_kana"]["rich_text"]:
        current_title_kana = props["title_kana"]["rich_text"][0]["text"]["content"]
    
    # リレーション情報の取得（新しいプロパティ名を使用）
    current_parent_id = None
    if props.get("relation_books_to", {}).get("relation") and props["relation_books_to"]["relation"]:
        current_parent_id = props["relation_books_to"]["relation"][0]["id"]
    
    current_children_ids = []
    if props.get("relation_books_from", {}).get("relation"):
        current_children_ids = [rel["id"] for rel in props["relation_books_from"]["relation"]]
    
    # 巻数情報
    current_owned = book.get("latest_owned_volume", 0)
    current_released = book.get("latest_released_volume", 0)
    current_completed = book.get("is_completed", False)
    
    # 画像URL
    current_image_url = book.get("image_url", "")
    
    # 発売日情報
    current_latest_release_date = datetime.date.today()
    if props.get("latest_release_date", {}).get("date"):
        try:
            date_str = props["latest_release_date"]["date"]["start"]
            current_latest_release_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            pass
    
    current_next_release_date = None
    if props.get("next_release_date", {}).get("date"):
        try:
            date_str = props["next_release_date"]["date"]["start"]
            current_next_release_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            pass
    
    # 詳細情報
    current_missing_volumes = ""
    if props.get("missing_volumes", {}).get("rich_text") and props["missing_volumes"]["rich_text"]:
        current_missing_volumes = props["missing_volumes"]["rich_text"][0]["text"]["content"]
    
    current_special_volumes = ""
    if props.get("special_volumes", {}).get("rich_text") and props["special_volumes"]["rich_text"]:
        current_special_volumes = props["special_volumes"]["rich_text"][0]["text"]["content"]
    
    current_owned_media = "単行本"
    if props.get("owned_media", {}).get("select"):
        current_owned_media = props["owned_media"]["select"]["name"]
    
    current_notes = ""
    if props.get("notes", {}).get("rich_text") and props["notes"]["rich_text"]:
        current_notes = props["notes"]["rich_text"][0]["text"]["content"]
    
    # 編集フォーム（BookFormFieldsコンポーネントを使用）
    with st.form("edit_book_form"):
        basic_info = BookFormFields.render_basic_info(
            default_title=current_title,
            default_title_kana=current_title_kana,
            default_magazine_type=current_magazine_type,
            default_magazine_name=current_magazine_name
        )
        title = basic_info["title"]
        title_kana = basic_info["title_kana"]
        magazine_type = basic_info["magazine_type"]
        magazine_name = basic_info["magazine_name"]
        
        # リレーション情報を取得
        try:
            all_mangas = manga_service.get_all_mangas()
        except Exception:
            all_mangas = []
        
        series_info = BookFormFields.render_series_selection(
            all_mangas=all_mangas,
            current_manga_id=book["id"],
            default_parent_id=current_parent_id
        )
        parent_id = series_info["parent_id"]
        children_ids = current_children_ids  # 編集時は既存の子作品を保持
        
        volume_info = BookFormFields.render_volume_info(
            default_owned=current_owned,
            default_released=current_released
        )
        latest_owned_volume = volume_info["latest_owned_volume"]
        latest_released_volume = volume_info["latest_released_volume"]
        
        uploaded_file = BookFormFields.render_image_info(
            current_image_url=current_image_url,
            is_edit_mode=True
        )
        
        if uploaded_file is not None:
            if cloudinary_enabled and cloudinary_available:
                st.info("📤 保存時にCloudinaryにアップロードされ、現在の画像と入れ替わります")
            else:
                st.warning("⚠️ Cloudinary設定が見つかりません")
        
        is_completed = BookFormFields.render_completion_status(default_completed=current_completed)
        
        latest_release_date, use_next_release_date, next_release_date = BookFormFields.render_date_info(
            default_latest_date=current_latest_release_date,
            default_next_date=current_next_release_date
        )
        
        detail_info = BookFormFields.render_detail_info(
            default_missing_volumes=current_missing_volumes,
            default_special_volumes=current_special_volumes,
            default_owned_media=current_owned_media,
            default_notes=current_notes
        )
        missing_volumes = detail_info["missing_volumes"]
        special_volumes = detail_info["special_volumes"]
        owned_media = detail_info["owned_media"]
        notes = detail_info["notes"]
        
        # 更新ボタン
        submitted = st.form_submit_button("💾 変更を保存", type="primary")
        
        if submitted:
            if not title or not magazine_type:
                st.error("❌ タイトルと連載誌タイプは必須項目です")
            elif latest_owned_volume > latest_released_volume:
                st.error("❌ 所持巻数が発売済み最新巻を超えています")
            else:
                try:
                    # ImageServiceを使用して画像を置き換え
                    final_image_url = current_image_url
                    
                    if uploaded_file is not None and image_service.is_available():
                        with st.spinner("画像をアップロード中..."):
                            final_image_url = image_service.replace_image(current_image_url, uploaded_file)
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
                    
                    # リレーション情報の準備
                    related_books_to = [parent_id] if parent_id else None
                    related_books_from = children_ids if children_ids else None
                    
                    # Mangaオブジェクトを作成
                    updated_manga = Manga(
                        id=book["id"],
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
                    
                    # MangaServiceを使用して更新
                    try:
                        with st.spinner("Notionを更新中..."):
                            success = manga_service.update_manga(updated_manga)
                            
                            # リレーション変更時の相互更新処理（親作品の変更のみ）
                            if success and parent_id != current_parent_id:
                                with st.spinner("シリーズ関係を更新中..."):
                                    manga_service.update_parent_relation(
                                        manga_id=book["id"],
                                        old_parent_id=current_parent_id,
                                        new_parent_id=parent_id
                                    )
                        
                                st.success("✅ 漫画情報が正常に更新されました！")
                                st.balloons()
                                
                                # かなが自動生成された場合は通知（AI生成の場合は明示）
                                if not title_kana.strip() and final_title_kana:
                                    if ai_generated:
                                        st.info(f"🤖 タイトルかなをAIで生成しました: **{final_title_kana}** (AI生成)")
                                    else:
                                        st.info(f"💡 タイトルかなを自動生成しました: {final_title_kana}")
                                
                                # セッション状態で更新成功をマーク
                                st.session_state.update_success = True
                            else:
                                st.error("❌ 更新に失敗しました")
                        
                    except Exception as update_error:
                        st.error(f"❌ 更新処理でエラーが発生しました: {str(update_error)}")
                    
                except Exception as e:
                    st.error(f"❌ 更新処理でエラーが発生しました: {str(e)}")
    
    # フォーム外で更新成功状態をチェック
    if st.session_state.get("update_success", False):
        st.success("🎉 更新が完了しました！")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📖 詳細に戻る", type="primary", use_container_width=True):
                st.session_state.update_success = False
                # MangaServiceを使用して更新されたデータを再取得
                try:
                    updated_manga = manga_service.get_manga_by_id(book["id"])
                    if updated_manga:
                        st.session_state.selected_book = updated_manga.to_dict()
                except:
                    pass  # エラー時は古いデータのまま
                
                st.session_state.page = "book_detail"
                st.rerun()
        
        with col2:
            if st.button("📚 一覧に戻る", use_container_width=True):
                st.session_state.update_success = False
                go_to_home()
                st.rerun()
