"""
Special Volume Detail Page: 特殊巻詳細画面
"""

import streamlit as st
from config.constants import DEFAULT_IMAGE_URL


def show_special_volume_detail(
    special_volume_service,
    manga_service
):
    """特殊巻詳細画面：選択された特殊巻の詳細情報表示"""
    from utils.session import SessionManager
    
    # 選択された特殊巻の確認
    selected_special_volume = SessionManager.get_selected_special_volume()
    if selected_special_volume is None:
        st.error("特殊巻が選択されていません")
        if st.button("ホームに戻る"):
            SessionManager.go_to_home()
            st.rerun()
        return
    
    # 特殊巻情報を取得
    special_volume = selected_special_volume
    
    # 親作品情報を取得
    try:
        parent_manga = manga_service.get_manga_by_id(special_volume.book_id)
    except Exception as e:
        st.error(f"親作品情報の取得に失敗しました: {str(e)}")
        parent_manga = None
    
    # ボタン群を水平配置
    st.markdown('<div class="detail-page-container">', unsafe_allow_html=True)
    st.markdown('<div class="detail-buttons-container">', unsafe_allow_html=True)
    
    # 3列レイアウト（戻る・空白・編集削除）
    home_col, spacer_col, action_col = st.columns([2, 1, 2])
    
    with home_col:
        if st.button("← ホームに戻る"):
            SessionManager.go_to_home()
            st.rerun()
    
    with action_col:
        # 編集・削除ボタンを入れ子の列で右揃え配置
        edit_col, delete_col = st.columns(2)
        with edit_col:
            if st.button("✏️ 編集"):
                # TODO: 特殊巻編集機能を後で実装
                st.info("特殊巻編集機能は後で実装予定")
        with delete_col:
            if st.button("🗑️ 削除", type="secondary"):
                # セッション状態の削除フラグを設定して、対話的削除を開始
                st.session_state.delete_special_volume_requested = True
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # detail-buttons-container終了
    
    # メインコンテンツを中央配置
    st.markdown('<div class="detail-content-container">', unsafe_allow_html=True)
    
    # 画像と基本情報を横並び表示
    image_col, info_col = st.columns([1, 2])
    
    with image_col:
        # 画像表示
        image_url = special_volume.image_url if special_volume.image_url else DEFAULT_IMAGE_URL
        st.image(
            image_url,
            caption=special_volume.title,
            width=300,
            use_column_width=True
        )
    
    with info_col:
        # タイトル
        st.markdown(f'<h1 class="book-title">{parent_manga.title} - {special_volume.title}</h1>', unsafe_allow_html=True)
        
        # 基本情報表示
        st.markdown("### 📚 基本情報")
        
        # タイプ（通常作品の連載状況のように表示）
        type_display = special_volume.type if special_volume.type else "特殊巻"
        if type_display == "特殊巻":
            type_badge = '<span class="status-badge status-ongoing">📔 特殊巻</span>'
        elif type_display == "外伝":
            type_badge = '<span class="status-badge status-completed">📖 外伝</span>'
        elif type_display == "ガイドブック":
            type_badge = '<span class="status-badge status-ongoing">📋 ガイドブック</span>'
        elif type_display == "映画":
            type_badge = '<span class="status-badge status-completed">🎬 映画</span>'
        elif type_display == "小説":
            type_badge = '<span class="status-badge status-ongoing">📕 小説</span>'
        else:
            type_badge = f'<span class="status-badge status-ongoing">📔 {type_display}</span>'
        
        st.markdown(type_badge, unsafe_allow_html=True)
        
        # 親作品情報
        st.markdown("**親作品:**")
        if st.button(f"📖 {parent_manga.title}", key="parent_manga_link"):
            SessionManager.go_to_detail(parent_manga)
            st.rerun()
        
        # その他の特殊巻表示
        if parent_manga:
            try:
                # 同じ親作品の他の特殊巻を取得
                all_special_volumes = special_volume_service.get_special_volumes_by_book_id(parent_manga.id)
                other_special_volumes = [sv for sv in all_special_volumes if sv.id != special_volume.id]
                
                if other_special_volumes:
                    st.markdown("---")
                    st.subheader("📔 その他の特殊巻")
                    
                    # 特殊巻をソート（type昇順、sort_order昇順）
                    sorted_volumes = sorted(other_special_volumes, key=lambda x: (x.type or "", x.sort_order or 0))
                    
                    # 2列表示で他の特殊巻を表示
                    for i in range(0, len(sorted_volumes), 2):
                        cols = st.columns(2)
                        
                        with cols[0]:
                            sv = sorted_volumes[i]
                            if st.button(f"📔 {sv.title}", key=f"other_sv_{sv.id}_0"):
                                SessionManager.go_to_special_volume_detail(sv)
                                st.rerun()
                        
                        if i + 1 < len(sorted_volumes):
                            with cols[1]:
                                sv = sorted_volumes[i + 1]
                                if st.button(f"📔 {sv.title}", key=f"other_sv_{sv.id}_1"):
                                    SessionManager.go_to_special_volume_detail(sv)
                                    st.rerun()
            
            except Exception as e:
                st.error(f"その他の特殊巻の取得に失敗しました: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)  # detail-content-container終了
    
    # 詳細ページコンテナを閉じる
    st.markdown('</div>', unsafe_allow_html=True)  # detail-page-container終了
    
    # 削除確認ダイアログの表示（@st.dialogを使用）
    if st.session_state.get('delete_special_volume_requested', False):
        @st.dialog("特殊巻削除確認")
        def confirm_delete_special_volume():
            st.warning(f"**{special_volume.title}** を削除しますか？")
            st.error("⚠️ この操作は取り消せません。")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ 削除する", type="primary", use_container_width=True):
                    try:
                        # 削除処理を実行
                        with st.spinner("削除中..."):
                            # 特殊巻データ削除
                            if special_volume_service.delete_special_volume(special_volume.id):
                                st.success("✅ 特殊巻を削除しました")
                                # セッション状態をクリア
                                st.session_state.selected_special_volume = None
                                st.session_state.delete_special_volume_requested = False
                                # ホームに戻る
                                SessionManager.go_to_home()
                                st.rerun()
                            else:
                                st.error("❌ 削除に失敗しました")
                    except Exception as e:
                        st.error(f"❌ 削除エラー: {str(e)}")
            
            with col2:
                if st.button("❌ キャンセル", use_container_width=True):
                    st.session_state.delete_special_volume_requested = False
                    st.rerun()
        
        # ダイアログを表示
        confirm_delete_special_volume()