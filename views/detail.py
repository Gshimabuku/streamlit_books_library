"""
Detail Page: Book detail view with edit/delete actions
"""

import streamlit as st
from datetime import datetime
from config.constants import DEFAULT_IMAGE_URL
from components.delete_dialog import DeleteDialog


def show_book_detail(
    special_volume_service,
    manga_service,
    image_service
):
    """詳細画面：選択された本の詳細情報表示"""
    from utils.session import SessionManager
    
    if st.session_state.selected_book is None:
        st.error("本が選択されていません")
        if st.button("ホームに戻る"):
            SessionManager.go_to_home()
            st.rerun()
        return
    
    book = st.session_state.selected_book
    
    # ボタン群を水平配置（PC右揃え、モバイル横並び）
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
                SessionManager.go_to_edit_book()
                st.rerun()
        with delete_col:
            if st.button("🗑️ 削除", type="secondary"):
                # 削除確認状態をセッションに保存
                st.session_state.show_delete_dialog = True
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # detail-buttons-container終了
    
    # Mangaオブジェクトから情報を取得（安全なアクセス）
    latest_release_date_obj = getattr(book, 'latest_release_date', None)
    latest_release_date = latest_release_date_obj.isoformat() if latest_release_date_obj is not None else ""
    
    next_release_date_obj = getattr(book, 'next_release_date', None)
    next_release_date = next_release_date_obj.isoformat() if next_release_date_obj is not None else ""
    
    missing_volumes = getattr(book, 'missing_volumes', '') or ""
    # special_volumesフィールドは廃止（別テーブルで管理）
    
    # 2列レイアウト
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 画像表示（エラーハンドリング付き）
        try:
            if book.image_url and book.image_url != "":
                st.image(book.image_url, width=300)
            else:
                st.image(DEFAULT_IMAGE_URL, width=300)
        except Exception as e:
            st.image(DEFAULT_IMAGE_URL, width=300)
    
    with col2:
        # タイトル
        title = getattr(book, 'title', 'タイトル不明')
        st.header(f"📚 {title}")
        
        # 漫画情報
        is_completed = getattr(book, 'is_completed', False)
        completion_status = "完結" if is_completed else "連載中"
        
        # 完結・連載中のステータスを背景色付きで表示
        if is_completed:
            status_color = "#28a745"  # 緑色（完結）
            text_color = "white"
        else:
            status_color = "#007bff"  # 青色（連載中）
            text_color = "white"
        
        status_class = "status-completed" if is_completed else "status-ongoing"
        st.markdown(f"""
        <div class="detail-status-badge {status_class}">
            {completion_status}
        </div>
        """, unsafe_allow_html=True)
        
        # 作品情報
        st.subheader("ℹ️ 作品情報")
        
        # 連載誌情報
        magazine_type = getattr(book, 'magazine_type', '')
        if magazine_type:
            magazine_display = magazine_type
            magazine_name = getattr(book, 'magazine_name', '')
            if magazine_name:
                magazine_display += f" - {magazine_name}"
            st.write(f"📰 **連載誌:** {magazine_display}")
        
        # 所持媒体情報
        owned_media = getattr(book, 'owned_media', '')
        if owned_media:
            st.write(f"💻 **所持媒体:** {owned_media}")
        
        # 最新巻情報
        latest_released_volume = getattr(book, 'latest_released_volume', 0)
        release_info = f"🆕 **最新巻:** {latest_released_volume}巻"
        if latest_release_date:
            try:
                date_obj = datetime.strptime(latest_release_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%Y年%m月%d日")
                release_info += f" [{formatted_date}発売]"
            except:
                release_info += f" [{latest_release_date}発売]"
        st.write(release_info)
        
        # 次巻発売日
        if next_release_date:
            try:
                date_obj = datetime.strptime(next_release_date, "%Y-%m-%d")
                formatted_next_date = date_obj.strftime("%Y年%m月%d日")
                st.write(f"⏭️ **次巻発売日:** {formatted_next_date}")
            except:
                st.write(f"⏭️ **次巻発売日:** {next_release_date}")
        
        st.markdown("---")
        
        # 所持状況
        st.subheader("📚 所持状況")
        
        # 所持巻数の計算
        owned_count = getattr(book, 'latest_owned_volume', 0)
        
        # 抜け巻がある場合の計算（新しいロジックに統一）
        if missing_volumes:
            try:
                missing_list = [vol.strip() for vol in missing_volumes.split(",") if vol.strip()]
                missing_count = len(missing_list)
                actual_owned = max(0, owned_count - missing_count)
            except:
                actual_owned = owned_count
        else:
            actual_owned = owned_count

        # 特殊巻数を取得（キャッシュ利用）
        special_volumes_list = []
        special_count = 0
        try:
            # キャッシュから特殊巻数を取得
            book_id = getattr(book, 'id', None)
            if book_id:
                special_count = special_volume_service.get_special_volume_count_for_book(book_id)
                
                # 詳細表示用に特殊巻リストも取得
                grouped_data = special_volume_service.get_all_special_volumes_grouped_by_book()
                special_volumes_list = grouped_data.get(book_id, [])
        except Exception as e:
            print(f"Error getting special volumes: {e}")

        # 所持冊数表示（通常巻 + 特殊巻）
        total_owned = actual_owned + special_count
        if special_count > 0:
            st.write(f"**所持巻数:** {actual_owned}巻 + 特殊巻{special_count}冊 = 合計{total_owned}冊")
        else:
            st.write(f"**所持巻数:** {actual_owned}巻")

        # 抜け巻
        if missing_volumes:
            st.write(f"**抜け巻:** {missing_volumes}")

        # 特殊巻一覧表示
        if special_volumes_list:
                st.markdown("---")

                # 特殊巻
                st.subheader("📔 特殊巻")
                
                # 特殊巻を表示（type昇順、sort_order昇順）
                sorted_volumes = sorted(special_volumes_list, key=lambda x: (x.type or "", x.sort_order or 0))
                
                # 特殊巻数に応じてレイアウトを調整
                if len(sorted_volumes) == 1:
                    sv = sorted_volumes[0]
                    if st.button(f"📔 {sv.title}", key=f"special_volume_{sv.id}"):
                        SessionManager.go_to_special_volume_detail(sv)
                        st.rerun()
                else:
                    # 2列表示
                    for i in range(0, len(sorted_volumes), 2):
                        cols = st.columns(2)
                        with cols[0]:
                            sv = sorted_volumes[i]
                            if st.button(f"📔 {sv.title}", key=f"special_volume_{sv.id}_0"):
                                SessionManager.go_to_special_volume_detail(sv)
                                st.rerun()
                        if i + 1 < len(sorted_volumes):
                            with cols[1]:
                                sv = sorted_volumes[i + 1]
                                if st.button(f"📔 {sv.title}", key=f"special_volume_{sv.id}_1"):
                                    SessionManager.go_to_special_volume_detail(sv)
                                    st.rerun()
    
    # 詳細ページコンテナを閉じる
    st.markdown('</div>', unsafe_allow_html=True)  # detail-page-container終了
    
    # 削除ダイアログの表示
    if st.session_state.get('show_delete_dialog', False):
        st.markdown("---")
        st.subheader("🗑️ 削除確認")
        
        def on_delete_success():
            """削除成功時のコールバック"""
            st.session_state.show_delete_dialog = False
            SessionManager.go_to_home()
        
        DeleteDialog.show(
            book=book,
            manga_service=manga_service,
            image_service=image_service,
            on_success_callback=on_delete_success
        )
