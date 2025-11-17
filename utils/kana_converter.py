"""
漢字・カタカナ→ひらがな変換ユーティリティ
タイトルの読み仮名（五十音順ソート用）を生成する
"""
import unicodedata

_kakasi_instance = None

def get_kakasi():
    """pykakasiインスタンスをシングルトンで取得"""
    global _kakasi_instance
    if _kakasi_instance is None:
        try:
            from pykakasi import kakasi
            kks = kakasi()
            _kakasi_instance = kks.convert
        except ImportError:
            # pykakasiがインストールされていない場合
            _kakasi_instance = None
    return _kakasi_instance

def title_to_kana(title: str) -> str:
    """
    タイトル文字列をひらがなに変換する
    
    Args:
        title: 元のタイトル（漢字・カタカナ・ひらがな混在OK）
    
    Returns:
        ひらがなに変換された文字列（五十音順ソート用）
    """
    if not title:
        return ""
    
    # Unicode正規化（全角・半角を統一）
    normalized = unicodedata.normalize("NFKC", title.strip())
    
    # pykakasiで変換
    converter = get_kakasi()
    if converter is None:
        # pykakasiが使えない場合はそのまま返す
        return normalized.lower()
    
    try:
        # pykakasiで変換（結果はリストで返される）
        result = converter(normalized)
        # 各要素の'hira'（ひらがな）を結合
        kana = "".join([item.get('hira', item.get('orig', '')) for item in result])
        return kana.strip()
    except Exception as e:
        # エラー時は元の文字列を返す
        print(f"かな変換エラー: {e}")
        return normalized.lower()
