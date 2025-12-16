"""
Add Special Volume Page: 特殊巻新規登録フォーム
"""

import streamlit as st
from services.special_volume_service import SpecialVolumeService
from services.manga_service import MangaService
from services.image_service import ImageService
from models.special_volume import SpecialVolume
from utils.session import SessionManager


def show_add_special_volume(
    special_volume_service: SpecialVolumeService,
    manga_service: MangaService,
    image_service: ImageService,
    go_to_home: callable,
    cloudinary_available: bool,
    cloudinary_enabled: bool
):
    """特殊巻新規登録画面"""
    st.header("📔 特殊巻を登録")
    
    # 戻るボタン
    if st.button("← ホームに戻る"):
        go_to_home()
        st.rerun()
    
    # 親作品一覧を取得
    try:
        all_mangas = manga_service.get_all_mangas()
        if not all_mangas:
            st.error("❌ 親作品が見つかりません。まず漫画を登録してください。")
            return
        
        # 作品をタイトルでソート
        sorted_mangas = sorted(all_mangas, key=lambda m: m.title_kana or m.title or "")
        manga_options = {f"{manga.title}": manga.id for manga in sorted_mangas}
        
    except Exception as e:
        st.error(f"❌ 作品データの取得に失敗しました: {str(e)}")
        return
    
    # 登録フォーム
    with st.form("special_volume_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 特殊巻タイトル
            title = st.text_input(
                "📚 特殊巻タイトル *",
                placeholder="例: 公式ガイドブック RED",
                help="特殊巻のタイトルを入力してください"
            )
            
            # 親作品選択
            parent_manga_title = st.selectbox(
                "📖 親作品 *",
                options=list(manga_options.keys()),
                help="この特殊巻が属する親作品を選択してください"
            )
            parent_manga_id = manga_options.get(parent_manga_title, "")
            
            # 作品タイプ
            type_options = ["特殊巻", "外伝", "ガイドブック", "映画", "小説"]
            volume_type = st.selectbox(
                "📋 作品タイプ *",
                type_options,
                help="特殊巻の種類を選択してください"
            )
            
            # ソート順
            sort_order = st.number_input(
                "🔢 ソート順",
                min_value=0.0,
                max_value=9999999999.0,  # 約100億まで対応
                value=0.0,
                step=0.1,
                format="%.1f",
                help="同じ親作品内での表示順序（小さい順に表示）\n例: 0巻→0、10.5巻→10.5、40億巻→4000000000"
            )
        
        with col2:
            # 画像アップロード
            st.subheader("🖼️ 画像")
            
            # Cloudinaryの利用可否表示
            if cloudinary_available and cloudinary_enabled:
                st.success("✅ 画像アップロード機能が利用できます")
                uploaded_file = st.file_uploader(
                    "画像を選択",
                    type=['png', 'jpg', 'jpeg', 'webp'],
                    help="推奨サイズ: 縦長の画像"
                )
            else:
                st.warning("⚠️ Cloudinary設定が無効のため、画像アップロード機能は利用できません")
                uploaded_file = None
            
            # 手動URL入力（代替手段）
            manual_image_url = st.text_input(
                "画像URL (手動入力)",
                placeholder="https://example.com/image.jpg",
                help="画像ファイルをアップロードできない場合の代替手段"
            )
        
        # 必須項目チェック用スペース
        st.markdown("---")
        
        # 登録ボタン
        submitted = st.form_submit_button("📔 特殊巻を登録", type="primary", use_container_width=False)
        
        if submitted:
            # 入力値検証
            if not title or not title.strip():
                st.error("❌ 特殊巻タイトルは必須項目です")
                return
            
            if not parent_manga_id:
                st.error("❌ 親作品を選択してください")
                return
            
            if not volume_type:
                st.error("❌ 作品タイプを選択してください")
                return
            
            try:
                # 画像処理
                final_image_url = None
                
                if uploaded_file is not None and image_service.is_available():
                    with st.spinner("画像をアップロード中..."):
                        final_image_url = image_service.upload_image(uploaded_file)
                        st.success(f"✅ 画像アップロード完了: {uploaded_file.name}")
                elif uploaded_file is not None:
                    st.warning("⚠️ Cloudinary設定がないため、画像はアップロードされませんでした")
                
                # 手動URL入力がある場合はそちらを優先
                if manual_image_url and manual_image_url.strip():
                    final_image_url = manual_image_url.strip()
                
                # SpecialVolumeオブジェクト作成
                new_special_volume = SpecialVolume(
                    id=None,  # 新規登録時はNone
                    title=title.strip(),
                    book_id=parent_manga_id,
                    sort_order=int(sort_order),
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