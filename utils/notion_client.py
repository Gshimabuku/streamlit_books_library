import requests
from typing import Any, Dict, List, Optional

"""
軽量なNotion APIユーティリティ
- query_notion(db_id, api_key=..., filter=..., page_size=..., sorts=...)
- create_notion_page(db_id, properties, api_key=...)

このモジュールはAPIキーを引数で受け取ることができ、ストリームリットのsecretsや環境変数と併用できます。
"""


def _build_headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }


def query_notion(
    db_id: str,
    api_key: str,
    filter: Optional[Dict[str, Any]] = None,
    page_size: int = 100,
    sorts: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Notionデータベースをクエリして`results`配列を返す。例外は呼び出し元で処理する。"""
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    payload: Dict[str, Any] = {}
    if filter:
        payload["filter"] = filter
    if page_size:
        payload["page_size"] = page_size
    if sorts:
        payload["sorts"] = sorts

    res = requests.post(url, headers=_build_headers(api_key), json=payload)
    res.raise_for_status()
    return res.json().get("results", [])


def create_notion_page(db_id: str, properties: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """Notionに新しいページ（データベースの行）を作成してレスポンスJSONを返す。"""
    url = "https://api.notion.com/v1/pages"
    payload = {"parent": {"database_id": db_id}, "properties": properties}
    res = requests.post(url, headers=_build_headers(api_key), json=payload)
    res.raise_for_status()
    return res.json()


def update_notion_page(page_id: str, properties: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """既存ページのプロパティ更新を行う。"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"properties": properties}
    res = requests.patch(url, headers=_build_headers(api_key), json=payload)
    res.raise_for_status()
    return res.json()


def retrieve_notion_page(page_id: str, api_key: str) -> Dict[str, Any]:
    """ページ単体を取得するラッパー。"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    res = requests.get(url, headers=_build_headers(api_key))
    res.raise_for_status()
    return res.json()
