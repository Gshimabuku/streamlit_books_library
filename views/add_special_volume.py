"""
Add Special Volume Page: 特殊巻新規登録フォーム
"""

import streamlit as st
from services.special_volume_service import SpecialVolumeService
from services.manga_service import MangaService
from services.image_service import ImageService
from models.special_volume import SpecialVolume
from components.book_form import BookFormFields
from utils.session import SessionManager


def show_add_special_volume(
    special_volume_service: SpecialVolumeService,
    manga_service: MangaService,
    image_service: ImageService,
    go_to_home: callable
):
    """特殊巻新規登録画面"""
    st.header("📔 特殊巻を登録")
    
    # 戻るボタン
    if st.button("← ホームに戻る"):
        go_to_home()
        st.rerun()
    
    with st.form("special_volume_form", clear_on_submit=False):
        # BookFormFieldsコンポーネントを使用
        basic_info = BookFormFields.render_special_volume_basic_info()
        title = basic_info["title"]
        volume_type = basic_info["type"]
        sort_order = basic_info["sort_order"]
        
        # 親作品情報を取得
        try:
            all_mangas = manga_service.get_all_mangas()
        except Exception:
            all_mangas = []
        
        parent_info = BookFormFields.render_parent_manga_selection(all_mangas)
        parent_manga_id = parent_info["parent_id"]
        parent_manga_title = parent_info["parent_title"]
        
        uploaded_file = BookFormFields.render_special_volume_image_info(image_service)
        
        # Cloudinaryが利用可能かチェック（プレビュー後のメッセージ）
        if uploaded_file is not None:
            if image_service.is_available():
                st.info("📤 登録時にCloudinaryにアップロードされます")
            else:
                st.warning("⚠️ Cloudinary設定が見つかりません。画像URLは保存されません。")
        
        # エンターキーでの送信を防ぐためのスペーサー
        st.markdown("---")
        
        # 登録ボタン
        submitted = st.form_submit_button("📋 特殊巻を登録", type="primary", use_container_width=False)
        
        if submitted:
            # フォームの検証
            validation_errors = BookFormFields.validate_special_volume_form(title, parent_manga_id)
            
            if validation_errors:
                for error in validation_errors:
                    st.error(f"❌ {error}")
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
                    

                    
                    # SpecialVolumeオブジェクト作成
                    new_special_volume = SpecialVolume(
                        id=None,  # 新規登録時はNone
                        title=title.strip(),
                        book_id=parent_manga_id,
                        sort_order=float(sort_order),  # float型で保存
                        type=volume_type,
                        image_url=final_image_url
                    )
                    
                    # SpecialVolumeServiceを使用して登録
                    with st.spinner("Notionに登録中..."):
                        result_id = special_volume_service.create_special_volume(new_special_volume)
                    
                    if result_id:
                        # キャッシュをクリア
                        SessionManager.clear_special_volumes_cache()
                        
                        st.success("✅ 特殊巻が正常に登録されました！")
                        st.balloons()
                        
                        # 画像URLがある場合は表示
                        if final_image_url:
                            st.markdown(f"🔗 [画像を開く]({final_image_url})")
                        
                        # 登録完了後の案内
                        st.info("📚 ホームページに戻って作品一覧を確認してください")
                        
                    else:
                        st.error("❌ 特殊巻の登録に失敗しました")
                        
                except Exception as e:
                    st.error(f"❌ 登録処理でエラーが発生しました: {str(e)}")
                    st.exception(e)  # デバッグ用