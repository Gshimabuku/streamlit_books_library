import streamlit as st
from utils.notion_client import query_notion, create_notion_page, update_notion_page, retrieve_notion_page
import datetime

# Cloudinaryのインポート（オプション）
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

# =========================
# アプリケーション設定
# =========================
st.set_page_config(
    page_title="Books Library",
    page_icon="📚",
    layout="wide"
)

# =========================
# Notion 設定
# =========================
try:
    NOTION_API_KEY = st.secrets["notion"]["api_key"]
    BOOKS_DATABASE_ID = st.secrets["notion"]["database_id"]
    
    # プレースホルダーチェック
    # if NOTION_API_KEY == "your_notion_api_key_here" or BOOKS_DATABASE_ID == "your_books_database_id_here":
    #     st.error("🔧 **Notion設定が必要です**")
    #     st.markdown("""
    #     ### 📋 設定手順
        
    #     1. **Notionでデータベースを作成**
    #        - 新しいページでデータベースを作成
    #        - 必要なプロパティを追加（title, latest_owned_volume, latest_released_volume, latest_release_date, is_completed など）
        
    #     2. **Notion APIキーを取得**
    #        - [Notion Developers](https://developers.notion.com/) にアクセス
    #        - 新しいインテグレーションを作成
    #        - APIキーをコピー
        
    #     3. **データベースIDを取得**
    #        - データベースのURLから32文字のIDをコピー
    #        - 例: `https://notion.so/your-workspace/DATABASE_ID?v=...`
        
    #     4. **設定ファイルを更新**
    #        - `.streamlit/secrets.toml` ファイルを編集
    #        - `api_key` と `database_id` を実際の値に置き換え
        
    #     5. **データベースにアクセス権限を付与**
    #        - データベースで「共有」をクリック
    #        - 作成したインテグレーションを招待
    #     """)
    #     st.stop()
        
except Exception as e:
    st.error(f"🔧 **Notion設定エラー**: {str(e)}")
    st.markdown("""
    ### 📋 secrets.toml ファイルを確認してください
    
    `.streamlit/secrets.toml` ファイルに以下の形式で設定が必要です：
    
    ```toml
    [notion]
    api_key = "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    database_id = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ```
    """)
    st.stop()

# =========================
# Cloudinary 設定
# =========================
if CLOUDINARY_AVAILABLE:
    try:
        cloudinary.config(
            cloud_name=st.secrets["cloudinary"]["cloud_name"],
            api_key=st.secrets["cloudinary"]["api_key"],
            api_secret=st.secrets["cloudinary"]["api_secret"]
        )
        CLOUDINARY_ENABLED = True
    except Exception:
        CLOUDINARY_ENABLED = False
else:
    CLOUDINARY_ENABLED = False

# =========================
# セッション状態の初期化
# =========================
if "page" not in st.session_state:
    st.session_state.page = "books_home"

if "selected_book" not in st.session_state:
    st.session_state.selected_book = None

# =========================
# ページ遷移関数
# =========================
def go_to_home():
    st.session_state.page = "books_home"
    st.session_state.selected_book = None

def go_to_detail(book_data):
    st.session_state.page = "book_detail"
    st.session_state.selected_book = book_data

def go_to_add_book():
    st.session_state.page = "add_book"

def go_to_edit_book():
    st.session_state.page = "edit_book"

# =========================
# メインアプリケーション
# =========================
def main():
    st.title("📚 Books Library")
    
    # ページ遷移に基づいてコンテンツを表示
    if st.session_state.page == "books_home":
        show_books_home()
    elif st.session_state.page == "book_detail":
        show_book_detail()
    elif st.session_state.page == "add_book":
        show_add_book()
    elif st.session_state.page == "edit_book":
        show_edit_book()

def show_books_home():
    """Home画面：本の一覧を3列グリッド表示"""
    st.header("📖 漫画ライブラリ")
    
    # 新規登録ボタン（常に表示）
    if st.button("➕ 新しい漫画を登録", type="primary"):
        st.session_state.page = "add_book"
        st.rerun()
    
    st.markdown("---")
    
    # データベース接続を試行（エラーでも継続）
    books = []
    
    try:
        # NotionDBから実際のデータを取得
        with st.spinner("データを読み込み中..."):
            sorts = [
                {
                    "property": "title", 
                    "direction": "ascending"
                }
            ]
            results = query_notion(BOOKS_DATABASE_ID, NOTION_API_KEY, sorts=sorts)
            
            # NotionDBのデータを表示用に変換
            for page in results:
                try:
                    props = page["properties"]
                    
                    # タイトル取得
                    title = "タイトル不明"
                    if props.get("title", {}).get("title"):
                        title = props["title"]["title"][0]["text"]["content"]
                    
                    # 画像URL取得
                    image_url = props.get("image_url", {}).get("url")
                    # 無効なURLの場合はNoneに設定
                    if not image_url or not image_url.startswith(('http://', 'https://')):
                        image_url = None
                    
                    # 巻数情報取得
                    latest_owned_volume = props.get("latest_owned_volume", {}).get("number", 0)
                    latest_released_volume = props.get("latest_released_volume", {}).get("number", 0)
                    
                    # 完結情報取得
                    is_completed = props.get("is_completed", {}).get("checkbox", False)
                    
                    book_data = {
                        "id": page["id"],
                        "title": title,
                        "image_url": image_url,
                        "latest_owned_volume": latest_owned_volume,
                        "latest_released_volume": latest_released_volume,
                        "is_completed": is_completed,
                        "page_data": page  # 詳細表示用に元データも保持
                    }
                    books.append(book_data)
                    
                except Exception as e:
                    st.error(f"データ読み込みエラー: {str(e)}")
                    continue
        
        # NotionDBから取得できなかった場合
        if not books:
            st.info("💡 まだ漫画が登録されていません。「新しい漫画を登録」ボタンから追加してください。")
        
    except Exception as e:
        error_message = str(e)
        if "401" in error_message or "Unauthorized" in error_message:
            st.error("🔐 **認証エラー**: Notion APIキーまたはデータベースIDが正しくありません")
            st.markdown("""
            ### 🔧 解決方法
            1. **APIキーを確認**: `.streamlit/secrets.toml` の `api_key` が正しいか確認
            2. **データベースIDを確認**: `database_id` が32文字の正しいIDか確認
            3. **アクセス権限を確認**: データベースにインテグレーションが招待されているか確認
            
            ### 📝 設定例
            ```toml
            [notion]
            api_key = "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
            database_id = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
            ```
            """)
        elif "403" in error_message or "Forbidden" in error_message:
            st.error("🚫 **アクセス権限エラー**: データベースへのアクセスが拒否されました")
            st.info("💡 Notionデータベースで「共有」→ インテグレーションを招待してください")
        else:
            st.warning(f"⚠️ NotionDBに接続できませんでした: {error_message}")
            st.info("📋 設定を確認するか、ダミーデータで動作をテストしてください。")
        
        # エラー時はダミーデータを表示
        books = [
            {
                "id": "book1",
                "title": "進撃の巨人",
                "image_url": None,  # 安全な画像URLに変更
                "latest_owned_volume": 32,
                "latest_released_volume": 34,
                "is_completed": True
            },
            {
                "id": "book2", 
                "title": "鬼滅の刃",
                "image_url": None,  # 安全な画像URLに変更
                "latest_owned_volume": 20,
                "latest_released_volume": 23,
                "is_completed": True
            },
            {
                "id": "book3",
                "title": "ワンピース",
                "image_url": None,  # 安全な画像URLに変更
                "latest_owned_volume": 105,
                "latest_released_volume": 108,
                "is_completed": False
            }
        ]
    
    # 本の一覧表示（データがある場合のみ）
    if books:
        # レスポンシブ3列グリッド表示（スマホ対応）
        cols = st.columns(3, gap="small")
        
        for i, book in enumerate(books):
            col = cols[i % 3]
            
            with col:
                # コンテナで全体をラップ
                with st.container(border=True):
                    # 本の画像（レスポンシブ対応）
                    try:
                        if book["image_url"] and book["image_url"] != "":
                            st.image(book["image_url"], use_container_width=True)
                        else:
                            # 画像がない場合はテキストで代替（スマホ対応サイズ）
                            st.markdown(f"""
                            <div style="
                                width: 100%; 
                                aspect-ratio: 3/4;
                                min-height: 120px;
                                max-height: 200px;
                                background-color: #f0f0f0; 
                                display: flex; 
                                align-items: center; 
                                justify-content: center; 
                                border-radius: 8px;
                                color: #666;
                                font-size: clamp(10px, 2.5vw, 14px);
                                margin-bottom: 8px;
                            ">
                                📚 画像なし
                            </div>
                            """, unsafe_allow_html=True)
                    except Exception as e:
                        # 画像読み込みエラー時の代替表示（スマホ対応）
                        st.markdown(f"""
                        <div style="
                            width: 100%; 
                            aspect-ratio: 3/4;
                            min-height: 120px;
                            max-height: 200px;
                            background-color: #f8f8f8; 
                            display: flex; 
                            align-items: center; 
                            justify-content: center; 
                            border-radius: 8px;
                            color: #999;
                            font-size: clamp(8px, 2vw, 12px);
                            margin-bottom: 8px;
                        ">
                            ⚠️ 画像読み込みエラー
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # タイトル（レスポンシブフォントサイズ）
                    st.markdown(f"""
                    <h3 style="
                        font-size: clamp(12px, 3vw, 18px);
                        margin: 8px 0 4px 0;
                        line-height: 1.2;
                        text-align: center;
                        overflow-wrap: break-word;
                    ">{book["title"]}</h3>
                    """, unsafe_allow_html=True)
                    
                    # 所持状況（コンパクト表示）
                    owned = book["latest_owned_volume"]
                    released = book["latest_released_volume"]
                    completion_status = "完結" if book["is_completed"] else "連載中"
                    
                    st.markdown(f"""
                    <div style="
                        font-size: clamp(10px, 2.5vw, 14px);
                        text-align: center;
                        margin: 4px 0;
                    ">
                        📖 {owned}/{released}巻<br>
                        📊 {completion_status}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 詳細ボタン（フルサイズ）
                    if st.button(f"詳細を見る", key=f"detail_{book['id']}", use_container_width=True):
                        go_to_detail(book)
                        st.rerun()

def show_book_detail():
    """詳細画面：選択された本の詳細情報表示"""
    if st.session_state.selected_book is None:
        st.error("本が選択されていません")
        if st.button("ホームに戻る"):
            go_to_home()
            st.rerun()
        return
    
    book = st.session_state.selected_book
    
    # 戻るボタン
    if st.button("← ホームに戻る"):
        go_to_home()
        st.rerun()
    
    st.header(f"📚 {book['title']}")
    
    # 2列レイアウト
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 画像表示（エラーハンドリング付き）
        try:
            if book["image_url"] and book["image_url"] != "":
                st.image(book["image_url"], width=300)
            else:
                st.markdown(f"""
                <div style="
                    width: 300px; 
                    height: 400px; 
                    background-color: #f0f0f0; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    border-radius: 8px;
                    color: #666;
                    font-size: 16px;
                ">
                    📚 画像なし
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"""
            <div style="
                width: 300px; 
                height: 400px; 
                background-color: #f8f8f8; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                border-radius: 8px;
                color: #999;
                font-size: 14px;
            ">
                ⚠️ 画像読み込みエラー
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📊 所持情報")
        st.write(f"**現在所持巻数:** {book['latest_owned_volume']}巻")
        st.write(f"**発売済み最新巻:** {book['latest_released_volume']}巻")
        st.write(f"**完結状況:** {'完結' if book['is_completed'] else '連載中'}")
        
        # 編集ボタン（今後実装）
        st.subheader("⚙️ 操作")
        if st.button("編集する"):
            go_to_edit_book()
            st.rerun()
        
        if st.button("削除する", type="secondary"):
            if st.session_state.get("confirm_delete", False):
                try:
                    # 削除機能の実装（今後）
                    st.success("削除機能は今後実装予定です")
                    st.session_state.confirm_delete = False
                except Exception as e:
                    st.error(f"削除に失敗しました: {str(e)}")
            else:
                st.session_state.confirm_delete = True
                st.warning("⚠️ 本当に削除しますか？もう一度「削除する」ボタンを押してください。")
                st.rerun()

def show_add_book():
    """新規漫画登録画面"""
    st.header("➕ 新しい漫画を登録")
    
    # 戻るボタン
    if st.button("← ホームに戻る"):
        go_to_home()
        st.rerun()
    
    with st.form("add_book_form"):
        st.subheader("📝 基本情報")
        
        # 必須項目
        title = st.text_input("漫画タイトル *", placeholder="例: 進撃の巨人")
        magazine_type = st.selectbox("連載誌タイプ *", ["ジャンプ", "マガジン", "サンデー", "その他"])
        magazine_name = st.text_input("連載誌名", placeholder="例: 週刊少年マガジン")
        
        # 巻数情報
        col1, col2 = st.columns(2)
        with col1:
            latest_owned_volume = st.number_input("現在所持巻数 *", min_value=0, value=1)
        with col2:
            latest_released_volume = st.number_input("発売済み最新巻 *", min_value=0, value=1)
        
        # その他情報
        st.subheader("📷 画像情報")
        
        # 画像アップロード方式選択
        upload_method = st.radio(
            "画像の追加方法を選択",
            ["ファイルをアップロード", "URLを直接入力"],
            horizontal=True
        )
        
        image_url = None
        
        if upload_method == "ファイルをアップロード":
            uploaded_file = st.file_uploader(
                "画像ファイルを選択", 
                type=["jpg", "jpeg", "png", "webp"],
                help="JPG、PNG、WEBP形式の画像ファイルをアップロードできます"
            )
            
            if uploaded_file is not None:
                # プレビュー表示
                st.image(uploaded_file, caption="アップロード予定の画像", width=200)
                
                # Cloudinaryが利用可能かチェック
                if CLOUDINARY_ENABLED and CLOUDINARY_AVAILABLE:
                    st.info("📤 登録時にCloudinaryにアップロードされます")
                else:
                    st.warning("⚠️ Cloudinary設定が見つかりません。画像URLは保存されません。")
        
        else:  # URLを直接入力
            image_url = st.text_input("画像URL", placeholder="https://example.com/image.jpg")
            
            if image_url:
                try:
                    st.image(image_url, caption="URLの画像プレビュー", width=200)
                except Exception:
                    st.warning("⚠️ 画像URLが正しくないか、読み込めません")
        
        synopsis = st.text_area("あらすじ", placeholder="漫画のあらすじを入力...")
        
        # 完結情報
        is_completed = st.checkbox("完結済み")
        
        # 日付情報
        st.subheader("📅 発売日情報")
        
        # 最新巻発売日（必須）
        latest_release_date = st.date_input(
            "最新巻発売日 *",
            value=datetime.date.today(),
            min_value=datetime.date(1960, 1, 1),
            max_value=datetime.date(2100, 12, 31),
            help="最新巻の発売日を設定します（必須項目）"
        )
        
        # 次巻発売予定日（オプション）
        use_next_release_date = st.checkbox("次巻発売予定日を登録する")
        next_release_date = st.date_input(
            "次巻発売予定日",
            value=datetime.date.today() + datetime.timedelta(days=90),
            min_value=datetime.date(1960, 1, 1),
            max_value=datetime.date(2100, 12, 31),
            help="上のチェックボックスをオンにした場合のみ登録されます"
        )
        
        # 詳細情報
        st.subheader("📚 詳細情報")
        missing_volumes = st.text_input("未所持巻（抜け）", placeholder="例: 3,5,10")
        special_volumes = st.text_input("特殊巻", placeholder="例: 0.5,10.5")
        owned_media = st.selectbox("所持媒体", ["単行本", "電子書籍", "両方"])
        notes = st.text_area("備考", placeholder="その他メモ...")
        
        # 登録ボタン
        submitted = st.form_submit_button("📚 漫画を登録", type="primary")
        
        if submitted:
            if not title or not magazine_type:
                st.error("❌ タイトルと連載誌タイプは必須項目です")
            else:
                try:
                    # 画像アップロード処理
                    final_image_url = None
                    
                    if upload_method == "ファイルをアップロード" and uploaded_file is not None:
                        if CLOUDINARY_ENABLED and CLOUDINARY_AVAILABLE:
                            with st.spinner("画像をアップロード中..."):
                                upload_result = cloudinary.uploader.upload(uploaded_file)
                                final_image_url = upload_result["secure_url"]
                                st.success(f"✅ 画像アップロード完了: {uploaded_file.name}")
                        else:
                            st.warning("⚠️ Cloudinary設定がないため、画像はアップロードされませんでした")
                    elif upload_method == "URLを直接入力" and image_url:
                        final_image_url = image_url
                    
                    # Notionページのプロパティ構築（段階的に拡張）
                    # 保存確認済み項目：title, latest_owned_volume, latest_released_volume, latest_release_date, is_completed
                    properties = {
                        "title": {"title": [{"text": {"content": title}}]},
                        "latest_owned_volume": {"number": latest_owned_volume},
                        "latest_released_volume": {"number": latest_released_volume},
                        "latest_release_date": {"date": {"start": latest_release_date.isoformat()}},
                        "is_completed": {"checkbox": is_completed}
                    }
                    
                    # 次巻発売予定日（チェックボックスの状態に基づいて）
                    if use_next_release_date and next_release_date:
                        properties["next_release_date"] = {"date": {"start": next_release_date.isoformat()}}
                    
                    # 追加プロパティ（段階的に実装）
                    # Select系プロパティ
                    if magazine_type:
                        properties["magazine_type"] = {"select": {"name": magazine_type}}
                    
                    # テキスト系プロパティ
                    if magazine_name:
                        properties["magazine_name"] = {"rich_text": [{"text": {"content": magazine_name}}]}
                    
                    if synopsis:
                        properties["synopsis"] = {"rich_text": [{"text": {"content": synopsis}}]}
                    
                    if missing_volumes:
                        properties["missing_volumes"] = {"rich_text": [{"text": {"content": missing_volumes}}]}
                    
                    if special_volumes:
                        properties["special_volumes"] = {"rich_text": [{"text": {"content": special_volumes}}]}
                    
                    if owned_media:
                        properties["owned_media"] = {"select": {"name": owned_media}}
                    
                    if notes:
                        properties["notes"] = {"rich_text": [{"text": {"content": notes}}]}
                    
                    # 画像URL（存在する場合のみ）
                    if final_image_url:
                        properties["image_url"] = {"url": final_image_url}
                    
                    if missing_volumes:
                        properties["missing_volumes"] = {"rich_text": [{"text": {"content": missing_volumes}}]}
                    
                    if special_volumes:
                        properties["special_volumes"] = {"rich_text": [{"text": {"content": special_volumes}}]}
                    
                    if owned_media:
                        properties["owned_media"] = {"rich_text": [{"text": {"content": owned_media}}]}
                    
                    if notes:
                        properties["notes"] = {"rich_text": [{"text": {"content": notes}}]}
                    
                    # デバッグ用：送信するプロパティを表示
                    with st.expander("🔍 デバッグ情報（送信データ）"):
                        st.json(properties)
                    
                    # 登録試行
                    try:
                        with st.spinner("Notionに登録中..."):
                            result = create_notion_page(BOOKS_DATABASE_ID, properties, NOTION_API_KEY)
                        
                        st.success("✅ 漫画が正常に登録されました！")
                        st.balloons()
                        
                        # デバッグ用：レスポンスを表示
                        with st.expander("🔍 デバッグ情報（レスポンス）"):
                            st.json(result)
                        
                        # 画像URLがある場合は表示
                        if final_image_url:
                            st.markdown(f"🔗 [画像を開く]({final_image_url})")
                        
                        # セッション状態で登録成功をマーク
                        st.session_state.registration_success = True
                        
                    except Exception as full_error:
                        st.error(f"❌ 全プロパティでの登録に失敗しました: {str(full_error)}")
                        
                        # 段階的再試行: まず基本プロパティ + 追加項目
                        st.warning("🔄 基本プロパティ + 追加項目で再試行します...")
                        
                        basic_plus_properties = {
                            "title": {"title": [{"text": {"content": title}}]},
                            "latest_owned_volume": {"number": latest_owned_volume},
                            "latest_released_volume": {"number": latest_released_volume},
                            "latest_release_date": {"date": {"start": latest_release_date.isoformat()}},
                            "is_completed": {"checkbox": is_completed}
                        }
                        
                        # 次巻発売予定日を追加
                        if use_next_release_date and next_release_date:
                            basic_plus_properties["next_release_date"] = {"date": {"start": next_release_date.isoformat()}}
                        
                        # テキスト系プロパティを段階的に追加
                        if magazine_type:
                            basic_plus_properties["magazine_type"] = {"select": {"name": magazine_type}}
                        if magazine_name:
                            basic_plus_properties["magazine_name"] = {"rich_text": [{"text": {"content": magazine_name}}]}
                        
                        with st.expander("🔍 基本プロパティ + 追加項目"):
                            st.json(basic_plus_properties)
                        
                        try:
                            with st.spinner("基本プロパティ + 追加項目で登録中..."):
                                result = create_notion_page(BOOKS_DATABASE_ID, basic_plus_properties, NOTION_API_KEY)
                            
                            st.success("✅ 基本プロパティ + 追加項目で登録成功！")
                            st.info("💡 一部のプロパティ（画像URL、詳細情報など）は保存されませんでした。")
                            
                            # セッション状態で登録成功をマーク
                            st.session_state.registration_success = True
                            
                        except Exception as basic_plus_error:
                            st.error(f"❌ 基本プロパティ + 追加項目でも失敗: {str(basic_plus_error)}")
                            
                            # 最後の手段: 最小限のプロパティのみ
                            st.warning("🔄 最小限のプロパティで最終再試行します...")
                            
                            minimal_properties = {
                                "title": {"title": [{"text": {"content": title}}]},
                                "latest_owned_volume": {"number": latest_owned_volume},
                                "latest_released_volume": {"number": latest_released_volume},
                                "is_completed": {"checkbox": is_completed},
                                "latest_release_date": {"date": {"start": latest_release_date.isoformat()}}
                            }
                            
                            with st.expander("🔍 最小限プロパティ"):
                                st.json(minimal_properties)
                            
                            try:
                                with st.spinner("最小限のプロパティで登録中..."):
                                    result = create_notion_page(BOOKS_DATABASE_ID, minimal_properties, NOTION_API_KEY)
                                
                                st.success("✅ 最小限のプロパティで登録成功！")
                                st.info("💡 基本情報のみ保存されました。詳細情報は後で編集してください。")
                                
                                # セッション状態で登録成功をマーク
                                st.session_state.registration_success = True
                                
                            except Exception as minimal_error:
                                st.error(f"❌ 最小限のプロパティでも登録失敗: {str(minimal_error)}")
                                
                                # 完全な失敗時のデバッグ情報
                                with st.expander("🔍 完全なエラー詳細とデバッグ情報"):
                                    st.write("**全プロパティ:**")
                                    st.json(properties)
                                    st.write("**基本プロパティ + 追加項目:**")
                                    st.json(basic_plus_properties)
                                    st.write("**最小限プロパティ:**")
                                    st.json(minimal_properties)
                                    st.write("**全プロパティエラー:**")
                                    st.code(str(full_error))
                                    st.write("**基本プロパティ + 追加項目エラー:**")
                                    st.code(str(basic_plus_error))
                                    st.write("**最小限プロパティエラー:**")
                                    st.code(str(minimal_error))
                                    st.write("**推奨対策:**")
                                    st.markdown("""
                                    1. Notionデータベースのプロパティ名を確認してください
                                    2. プロパティの型（rich_text、number、checkbox、url、date）が正しいか確認してください
                                    3. データベースIDが正しいか確認してください
                                    4. APIキーに適切な権限があるか確認してください
                                    """)
                    
                except Exception as e:
                    st.error(f"❌ 登録処理でエラーが発生しました: {str(e)}")
                    
                    # デバッグ用：送信しようとしたプロパティを表示
                    with st.expander("🔍 エラー詳細とデバッグ情報"):
                        st.write("**送信しようとしたプロパティ:**")
                        st.json(properties)
                        st.write("**エラーの詳細:**")
                        st.code(str(e))
    # フォーム外で登録成功状態をチェック
    if st.session_state.get("registration_success", False):
        st.success("🎉 登録が完了しました！")
        if st.button("📚 ホームに戻る", type="primary"):
            st.session_state.registration_success = False  # フラグをリセット
            go_to_home()
            st.rerun()

def show_edit_book():
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
    
    st.info("📝 編集機能は今後実装予定です")
    st.write(f"選択中の漫画: **{book['title']}**")

if __name__ == "__main__":
    main()
