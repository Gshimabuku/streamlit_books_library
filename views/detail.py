"""
Detail Page: Book detail view with edit/delete actions
"""

import streamlit as st
from datetime import datetime
from services.manga_service import MangaService
from components.delete_dialog import DeleteDialog
from config.constants import DEFAULT_IMAGE_URL


def show_book_detail(
    go_to_home: callable,
    go_to_edit_book: callable,
    confirm_delete_dialog: callable
):
    """詳細画面：選択された本の詳細情報表示"""
    from utils.session import SessionManager
    
    # ページトップアンカーを設置
    st.markdown('<div id="page-top" class="page-top-anchor"></div>', unsafe_allow_html=True)
    
    # スクロール位置をトップにリセット（ページ遷移時のみ）
    if SessionManager.should_scroll_to_top():
        st.markdown("""
        <script>
        // 複数の方法でスクロールをトップに戻す
        setTimeout(function() {
            // 方法1: 直接スクロール
            window.scrollTo({
                top: 0,
                behavior: 'instant'
            });
            
            // 方法2: bodyのスクロールもリセット
            document.body.scrollTop = 0;
            document.documentElement.scrollTop = 0;
            
            // 方法3: アンカーを使用
            const topAnchor = document.getElementById('page-top');
            if (topAnchor) {
                topAnchor.scrollIntoView({behavior: 'instant'});
            }
        }, 50);
        </script>
        """, unsafe_allow_html=True)
        SessionManager.reset_scroll_flag()
    
    if st.session_state.selected_book is None:
        st.error("本が選択されていません")
        if st.button("ホームに戻る"):
            go_to_home()
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
            go_to_home()
            st.rerun()
    
    with action_col:
        # 編集・削除ボタンを入れ子の列で右揃え配置
        edit_col, delete_col = st.columns(2)
        with edit_col:
            if st.button("✏️ 編集"):
                go_to_edit_book()
                st.rerun()
        with delete_col:
            if st.button("🗑️ 削除", type="secondary"):
                confirm_delete_dialog()
    
    st.markdown('</div>', unsafe_allow_html=True)  # detail-buttons-container終了
    
    # Notionから詳細データを取得
    page_data = book.get("page_data", {})
    props = page_data.get("properties", {})
    
    # 追加情報を取得
    latest_release_date = ""
    if props.get("latest_release_date", {}).get("date"):
        latest_release_date = props["latest_release_date"]["date"]["start"]
    
    next_release_date = ""
    if props.get("next_release_date", {}).get("date"):
        next_release_date = props["next_release_date"]["date"]["start"]
    
    missing_volumes = ""
    if props.get("missing_volumes", {}).get("rich_text") and props["missing_volumes"]["rich_text"]:
        missing_volumes = props["missing_volumes"]["rich_text"][0]["text"]["content"]
    
    special_volumes = ""
    if props.get("special_volumes", {}).get("rich_text") and props["special_volumes"]["rich_text"]:
        special_volumes = props["special_volumes"]["rich_text"][0]["text"]["content"]
    
    # 2列レイアウト
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 画像表示（エラーハンドリング付き）
        try:
            if book["image_url"] and book["image_url"] != "":
                st.image(book["image_url"], width=300)
            else:
                st.image(DEFAULT_IMAGE_URL, width=300)
        except Exception as e:
            st.image(DEFAULT_IMAGE_URL, width=300)
    
    with col2:
        # タイトル
        st.header(f"📚 {book['title']}")
        
        # 漫画情報
        completion_status = "完結" if book['is_completed'] else "連載中"
        
        # 完結・連載中のステータスを背景色付きで表示
        if book['is_completed']:
            status_color = "#28a745"  # 緑色（完結）
            text_color = "white"
        else:
            status_color = "#007bff"  # 青色（連載中）
            text_color = "white"
        
        status_class = "status-completed" if book['is_completed'] else "status-ongoing"
        st.markdown(f"""
        <div class="detail-status-badge {status_class}">
            {completion_status}
        </div>
        """, unsafe_allow_html=True)
        
        # シリーズ情報
        relation_books_to = props.get('relation_books_to', {}).get('relation', [])
        relation_books_from = props.get('relation_books_from', {}).get('relation', [])
        
        # if relation_books_to or relation_books_from:
        #     st.markdown("### 🔗 シリーズ情報")
            
        #     # 親作品がある場合
        #     if relation_books_to:
        #         st.write(f"📤 **親作品:** この作品は続編・外伝・スピンオフです")
        #         # 実際の親作品名を表示する場合は、MangaServiceで取得が必要
                
        #     # 子作品がある場合
        #     if relation_books_from:
        #         child_count = len(relation_books_from)
        #         st.write(f"📥 **子作品:** {child_count}件の続編・外伝・スピンオフがあります")
        
        # st.markdown("---")
        
        # 連載誌情報
        magazine_type = book.get('magazine_type', '')
        magazine_name = book.get('page_data', {}).get('properties', {}).get('magazine_name', {}).get('rich_text', [])
        if magazine_name and magazine_name[0].get('text', {}).get('content'):
            magazine_name_text = magazine_name[0]['text']['content']
            st.write(f"📰 **連載誌:** {magazine_type} - {magazine_name_text}")
        elif magazine_type:
            st.write(f"📰 **連載誌:** {magazine_type}")
        
        # 所持媒体情報
        owned_media = props.get('owned_media', {}).get('select')
        if owned_media:
            owned_media_name = owned_media.get('name', '単行本')
            if owned_media_name != '単行本':
                st.write(f"💻 **所持媒体:** {owned_media_name}")
        
        st.markdown("---")
        
        # 最新巻情報
        release_info = f"**最新巻:** {book['latest_released_volume']}巻"
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
                st.write(f"**次巻発売日:** {formatted_next_date}")
            except:
                st.write(f"**次巻発売日:** {next_release_date}")
        
        st.markdown("---")
        
        # 所持状況
        st.subheader("📚 所持状況")
        
        # 所持巻数の計算
        owned_count = book['latest_owned_volume']
        missing_count = 0
        
        # 抜け巻がある場合の計算
        if missing_volumes:
            try:
                missing_list = [vol.strip() for vol in missing_volumes.split(",") if vol.strip()]
                missing_count = len(missing_list)
                actual_owned = owned_count - missing_count
                st.write(f"**所持巻数:** {actual_owned}巻")
            except:
                st.write(f"**所持巻数:** {owned_count}巻")
        else:
            st.write(f"**所持巻数:** {owned_count}巻")

        # 抜け巻
        if missing_volumes:
            st.write(f"**抜け巻:** {missing_volumes}")
        
        # 特殊巻（廃止 - 新しい特殊巻テーブルで管理）
        # if special_volumes:
        #     st.write(f"**特殊巻:** {special_volumes}")
    
    # 特殊巻一覧表示（新システム）
    st.markdown("### 📚 特殊巻")
    try:
        # 詳細ページの関数にspecial_volume_serviceパラメータが渡されるまでの暫定対応
        if 'special_volume_service' in st.session_state:
            special_volumes = st.session_state.special_volume_service.get_special_volumes_by_book_id(book.get('id'))
            if special_volumes:
                st.markdown("この作品に関連する特殊巻:")
                for sv in sorted(special_volumes, key=lambda x: x.sort_order or 0):
                    st.markdown(f"• {sv.title}")
            else:
                st.markdown("*関連する特殊巻はありません*")
        else:
            st.info("特殊巻機能を利用するには、アプリケーションの更新が必要です。")
    except Exception as sv_error:
        st.warning(f"⚠️ 特殊巻データの読み込みでエラーが発生しました: {sv_error}")
    
    # 詳細ページコンテナを閉じる
    st.markdown('</div>', unsafe_allow_html=True)  # detail-page-container終了
