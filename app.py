import streamlit as st
from notion_client import Client
import cloudinary
import cloudinary.uploader
import datetime

# =========================
# Notion 設定
# =========================
NOTION_API_KEY = st.secrets["notion"]["api_key"]
DATABASE_ID = st.secrets["notion"]["database_id"]
notion = Client(auth=NOTION_API_KEY)

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
        with st.spinner("Cloudinaryにアップロード中..."):
            # Cloudinaryにアップロード
            upload_result = cloudinary.uploader.upload(uploaded_file)

        image_url = upload_result["secure_url"]

        # Notion に登録
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": uploaded_file.name}}]},
                "ImageURL": {"url": image_url},
                "UploadedAt": {"date": {"start": datetime.datetime.now().isoformat()}}
            }
        )

        st.success("✅ アップロード完了！NotionにURLを保存しました。")
        st.markdown(f"📎 [Cloudinaryで開く]({image_url})")

# =========================
# 画像一覧（オプション）
# =========================
if st.button("📖 Notionに登録された画像一覧を表示"):
    results = notion.databases.query(database_id=DATABASE_ID)
    st.subheader("登録済み画像一覧")
    for page in results["results"]:
        name = page["properties"]["Name"]["title"][0]["text"]["content"]
        image_url = page["properties"]["ImageURL"]["url"]
        st.markdown(f"**{name}**")
        st.image(image_url, use_container_width=True)
