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
    
    # Mangaオブジェクトから既存データを取得
    current_title = getattr(book, 'title', '')
    current_magazine_type = getattr(book, 'magazine_type', 'その他')
    current_magazine_name = getattr(book, 'magazine_name', '')
    current_title_kana = getattr(book, 'title_kana', '')
    
    # リレーション情報の取得
    current_parent_id = None
    current_children_ids = []
    
    # related_books_toがリストで、最初の要素がID
    related_books_to = getattr(book, 'related_books_to', None)
    if related_books_to and len(related_books_to) > 0:
        current_parent_id = related_books_to[0]
    
    # related_books_fromがリストで、全てがID
    related_books_from = getattr(book, 'related_books_from', None)
    if related_books_from:
        current_children_ids = related_books_from
    
    # 巻数情報
    current_owned = getattr(book, 'latest_owned_volume', 0)
    current_released = getattr(book, 'latest_released_volume', 0)
    current_completed = getattr(book, 'is_completed', False)
    
    # 画像URL
    current_image_url = getattr(book, 'image_url', '')
    
    # 発売日情報
    current_latest_release_date = getattr(book, 'latest_release_date', None)
    if current_latest_release_date is None:
        current_latest_release_date = datetime.date.today()
    
    current_next_release_date = getattr(book, 'next_release_date', None)
    
    # 詳細情報
    current_missing_volumes = getattr(book, 'missing_volumes', '')
    current_special_volumes = getattr(book, 'special_volumes', '')
    current_owned_media = getattr(book, 'owned_media', '単行本')
    current_notes = getattr(book, 'notes', '')
    
    # 編集フォーム（BookFormFieldsコンポーネントを使用）
    with st.form("edit_book_form", clear_on_submit=False):
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
            current_manga_id=getattr(book, 'id', None),
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
        
        # エンターキーでの送信を防ぐためのスペーサー
        st.markdown("---")
        
        # 更新ボタン
        submitted = st.form_submit_button("💾 変更を保存", type="primary", use_container_width=False)
        
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
                    
                    # 日付フィールドの検証と変換
                    try:
                        # latest_release_dateの型確認
                        if hasattr(latest_release_date, 'date'):
                            latest_release_date = latest_release_date.date()
                        elif isinstance(latest_release_date, str):
                            latest_release_date = datetime.datetime.strptime(latest_release_date, "%Y-%m-%d").date()
                        
                        # next_release_dateの型確認
                        if use_next_release_date and next_release_date:
                            if hasattr(next_release_date, 'date'):
                                next_release_date = next_release_date.date()
                            elif isinstance(next_release_date, str):
                                next_release_date = datetime.datetime.strptime(next_release_date, "%Y-%m-%d").date()
                        else:
                            next_release_date = None
                            
                    except Exception as date_error:
                        st.error(f"❌ 日付フィールドの変換エラー: {str(date_error)}")
                        return
                    
                    # Mangaオブジェクトを作成
                    updated_manga = Manga(
                        id=getattr(book, 'id', None),
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
                        next_release_date=next_release_date,
                        missing_volumes=missing_volumes,
                        special_volumes="",  # 特殊巻は別テーブルで管理
                        owned_media=owned_media,
                        notes=notes
                    )
                    
                    # データ検証
                    if not updated_manga.id:
                        st.error("❌ 漫画IDが見つかりません。")
                        return
                    
                    if not updated_manga.title or not updated_manga.title.strip():
                        st.error("❌ タイトルが空です。")
                        return
                    
                    # MangaServiceを使用して更新
                    with st.spinner("Notionを更新中..."):
                        try:
                            # プロパティ生成のテスト
                            try:
                                test_properties = updated_manga.to_notion_properties()
                                print(f"Generated properties for update: {test_properties}")
                            except Exception as prop_error:
                                st.error(f"❌ データ変換エラー: {str(prop_error)}")
                                return
                            
                            success = manga_service.update_manga(updated_manga)
                            
                            if success:
                                # 特殊巻キャッシュをクリア（更新時にデータが変更される可能性があるため）
                                from utils.session import SessionManager
                                SessionManager.clear_special_volumes_cache()
                                
                                # リレーション変更時の相互更新処理（親作品の変更のみ）
                                if parent_id != current_parent_id:
                                    with st.spinner("シリーズ関係を更新中..."):
                                        relation_success = manga_service.update_parent_relation(
                                            manga_id=getattr(book, 'id', None),
                                            old_parent_id=current_parent_id,
                                            new_parent_id=parent_id
                                        )
                                        if not relation_success:
                                            st.warning("⚠️ シリーズ関係の更新で問題が発生しました")
                                
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
                            st.error(f"エラータイプ: {type(update_error)}")
                            
                            # 更新しようとしたデータをデバッグ表示
                            with st.expander("🔍 デバッグ情報"):
                                st.write("更新しようとした漫画データ:")
                                st.json({
                                    "id": updated_manga.id,
                                    "title": updated_manga.title,
                                    "latest_owned_volume": updated_manga.latest_owned_volume,
                                    "latest_released_volume": updated_manga.latest_released_volume
                                })
                            
                            st.exception(update_error)  # デバッグ用の詳細エラー表示
                    
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
                    book_id = getattr(book, 'id', None)
                    if book_id:
                        updated_manga = manga_service.get_manga_by_id(book_id)
                        if updated_manga:
                            st.session_state.selected_book = updated_manga
                except:
                    pass  # エラー時は古いデータのまま
                
                st.session_state.page = "book_detail"
                st.rerun()
        
        with col2:
            if st.button("📚 一覧に戻る", use_container_width=True):
                st.session_state.update_success = False
                go_to_home()
                st.rerun()
