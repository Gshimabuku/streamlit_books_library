import streamlit as st
from utils.notion_client import query_notion, create_notion_page
import cloudinary
import cloudinary.uploader
import datetime

# =========================
# Notion 設定
# =========================
NOTION_API_KEY = st.secrets["notion"]["api_key"]
DATABASE_ID = st.secrets["notion"]["database_id"]

# =========================
# Cloudinary 設定
# =========================
cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)

# =========================
# Streamlit UI
# =========================
st.title("🖼️ Cloudinary + Notion 画像アップロード")

uploaded_file = st.file_uploader("画像ファイルを選択してください", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="アップロード画像プレビュー", use_container_width=True)

    if st.button("アップロードしてNotionに保存"):
        try:
            with st.spinner("Cloudinaryにアップロード中..."):
                # Cloudinaryにアップロード
                upload_result = cloudinary.uploader.upload(uploaded_file)

            image_url = upload_result["secure_url"]

            # Notion に登録
            with st.spinner("Notionに保存中..."):
                page_data = {
                    "Name": {"title": [{"text": {"content": uploaded_file.name}}]},
                    "ImageURL": {"url": image_url},
                    "UploadedAt": {"date": {"start": datetime.datetime.now().isoformat()}}
                }
                create_notion_page(NOTION_API_KEY, DATABASE_ID, page_data)

            st.success("✅ アップロード完了！NotionにURLを保存しました。")
            st.markdown(f"📎 [Cloudinaryで開く]({image_url})")
            
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
            st.info("Cloudinary設定とNotion設定を確認してください。")
        st.markdown(f"📎 [Cloudinaryで開く]({image_url})")

# =========================
# 画像一覧（オプション）
# =========================
if st.button("📖 Notionに登録された画像一覧を表示"):
    try:
        # カスタムユーティリティを使用してデータベースをクエリ
        sorts = [
            {
                "property": "UploadedAt",
                "direction": "descending"
            }
        ]
        results = query_notion(NOTION_API_KEY, DATABASE_ID, sorts=sorts)
        st.subheader("登録済み画像一覧")
        
        if results.get("results"):
            for page in results["results"]:
                # プロパティの存在確認とエラーハンドリング
                try:
                    name_prop = page["properties"].get("Name", {})
                    if name_prop.get("title") and len(name_prop["title"]) > 0:
                        name = name_prop["title"][0]["text"]["content"]
                    else:
                        name = "名前なし"
                    
                    image_url_prop = page["properties"].get("ImageURL", {})
                    if image_url_prop.get("url"):
                        image_url = image_url_prop["url"]
                        st.markdown(f"**{name}**")
                        st.image(image_url, use_container_width=True)
                    else:
                        st.markdown(f"**{name}** - 画像URLなし")
                except Exception as e:
                    st.error(f"ページの読み込みエラー: {str(e)}")
        else:
            st.info("登録された画像がありません。")
    except Exception as e:
        st.error(f"Notionデータベースの取得に失敗しました: {str(e)}")
        st.info("データベースIDとAPIキーを確認してください。")
