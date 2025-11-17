"""
漢字・カタカナ・ローマ字→ひらがな変換ユーティリティ
タイトルの読み仮名（五十音順ソート用）を生成する
英語・ローマ字も日本語に変換する
AI（LLM）を使用してより正確な変換も可能
"""
import unicodedata
import re
import os

_kakasi_instance = None
_cutlet_instance = None

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

def get_cutlet():
    """cutletインスタンスをシングルトンで取得（英語→ローマ字→カタカナ）"""
    global _cutlet_instance
    if _cutlet_instance is None:
        try:
            import cutlet
            _cutlet_instance = cutlet.Cutlet()
        except ImportError:
            _cutlet_instance = None
    return _cutlet_instance

def romaji_to_hiragana(text: str) -> str:
    """
    ローマ字をひらがなに変換する
    英語の単語も可能な限り日本語発音に近づける
    """
    # ローマ字→ひらがな変換テーブル
    romaji_map = {
        # 4文字のローマ字
        'tchi': 'っち',
        # 3文字のローマ字（長い方から優先）
        'kya': 'きゃ', 'kyu': 'きゅ', 'kyo': 'きょ',
        'sha': 'しゃ', 'shu': 'しゅ', 'sho': 'しょ', 'shi': 'し',
        'cha': 'ちゃ', 'chu': 'ちゅ', 'cho': 'ちょ', 'chi': 'ち',
        'nya': 'にゃ', 'nyu': 'にゅ', 'nyo': 'にょ',
        'hya': 'ひゃ', 'hyu': 'ひゅ', 'hyo': 'ひょ',
        'mya': 'みゃ', 'myu': 'みゅ', 'myo': 'みょ',
        'rya': 'りゃ', 'ryu': 'りゅ', 'ryo': 'りょ',
        'gya': 'ぎゃ', 'gyu': 'ぎゅ', 'gyo': 'ぎょ',
        'jya': 'じゃ', 'jyu': 'じゅ', 'jyo': 'じょ',
        'bya': 'びゃ', 'byu': 'びゅ', 'byo': 'びょ',
        'pya': 'ぴゃ', 'pyu': 'ぴゅ', 'pyo': 'ぴょ',
        'tsu': 'つ', 'dzu': 'づ',
        'tth': 'っす', 'cch': 'っち', 'cck': 'っく',
        # 2文字のローマ字
        'ka': 'か', 'ki': 'き', 'ku': 'く', 'ke': 'け', 'ko': 'こ',
        'sa': 'さ', 'si': 'し', 'su': 'す', 'se': 'せ', 'so': 'そ',
        'ta': 'た', 'ti': 'ち', 'tu': 'つ', 'te': 'て', 'to': 'と',
        'na': 'な', 'ni': 'に', 'nu': 'ぬ', 'ne': 'ね', 'no': 'の',
        'ha': 'は', 'hi': 'ひ', 'hu': 'ふ', 'fu': 'ふ', 'he': 'へ', 'ho': 'ほ',
        'ma': 'ま', 'mi': 'み', 'mu': 'む', 'me': 'め', 'mo': 'も',
        'ya': 'や', 'yi': 'い', 'yu': 'ゆ', 'ye': 'いぇ', 'yo': 'よ',
        'ra': 'ら', 'ri': 'り', 'ru': 'る', 're': 'れ', 'ro': 'ろ',
        'la': 'ら', 'li': 'り', 'lu': 'る', 'le': 'れ', 'lo': 'ろ',
        'wa': 'わ', 'wi': 'うぃ', 'wu': 'う', 'we': 'うぇ', 'wo': 'を',
        'ga': 'が', 'gi': 'ぎ', 'gu': 'ぐ', 'ge': 'げ', 'go': 'ご',
        'za': 'ざ', 'zi': 'じ', 'zu': 'ず', 'ze': 'ぜ', 'zo': 'ぞ',
        'ja': 'じゃ', 'ji': 'じ', 'ju': 'じゅ', 'je': 'じぇ', 'jo': 'じょ',
        'da': 'だ', 'di': 'ぢ', 'du': 'づ', 'de': 'で', 'do': 'ど',
        'ba': 'ば', 'bi': 'び', 'bu': 'ぶ', 'be': 'べ', 'bo': 'ぼ',
        'pa': 'ぱ', 'pi': 'ぴ', 'pu': 'ぷ', 'pe': 'ぺ', 'po': 'ぽ',
        'va': 'ゔぁ', 'vi': 'ゔぃ', 'vu': 'ゔ', 've': 'ゔぇ', 'vo': 'ゔぉ',
        'fa': 'ふぁ', 'fi': 'ふぃ', 'fe': 'ふぇ', 'fo': 'ふぉ',
        # 英語でよく使われる組み合わせ
        'th': 'す', 'dh': 'ず', 'ng': 'んぐ',
        # 1文字
        'a': 'あ', 'i': 'い', 'u': 'う', 'e': 'え', 'o': 'お',
        'n': 'ん', 'l': 'る', 'r': 'る', 'v': 'ゔ', 'f': 'ふ',
        'x': 'くす', 'q': 'く', 'c': 'く', 'd': 'ど', 'g': 'ぐ',
        'b': 'ぶ', 'p': 'ぷ', 's': 'す', 't': 'と', 'y': 'い', 'w': 'う',
    }
    
    result = []
    text_lower = text.lower()
    i = 0
    
    while i < len(text_lower):
        matched = False
        # 長いローマ字から順に試す（4文字、3文字、2文字、1文字）
        for length in [4, 3, 2, 1]:
            if i + length <= len(text_lower):
                substr = text_lower[i:i+length]
                if substr in romaji_map:
                    result.append(romaji_map[substr])
                    i += length
                    matched = True
                    break
        
        if not matched:
            # 変換できない文字（スペースや記号など）はそのまま
            result.append(text_lower[i])
            i += 1
    
    return ''.join(result)

def title_to_kana_with_ai(title: str, api_key: str = None, provider: str = "openai") -> str:
    """
    AIを使用して漫画タイトルをひらがなに変換する
    より正確で文脈を理解した変換が可能
    
    Args:
        title: 漫画タイトル
        api_key: APIキー（環境変数OPENAI_API_KEYまたはANTHROPIC_API_KEYから取得可能）
        provider: "openai" または "anthropic"
    
    Returns:
        ひらがなに変換された文字列
    """
    if not title:
        return ""
    
    # APIキーの取得
    if api_key is None:
        if provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
        elif provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        # APIキーがない場合は通常の変換にフォールバック
        return title_to_kana(title)
    
    try:
        if provider == "openai":
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは漫画タイトルを正確なひらがなの読み仮名に変換する専門家です。タイトルの正式な読み方をひらがなのみで出力してください。記号やスペースは含めず、純粋なひらがなのみ（伸ばし棒「ー」は含める）を出力してください。"
                    },
                    {
                        "role": "user",
                        "content": f"次の漫画タイトルをひらがなに変換してください（ひらがなのみで出力）: {title}"
                    }
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            kana = response.choices[0].message.content.strip()
            # ひらがな以外を除去
            kana = re.sub(r'[^\u3040-\u309F]', '', kana)
            return kana
            
        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": f"次の漫画タイトルを正確なひらがなの読み仮名に変換してください。ひらがなのみ（伸ばし棒「ー」含む）で出力し、記号やスペースは含めないでください: {title}"
                    }
                ]
            )
            
            kana = message.content[0].text.strip()
            # ひらがな以外を除去
            kana = re.sub(r'[^\u3040-\u309F]', '', kana)
            return kana
            
    except Exception as e:
        print(f"AI変換エラー: {e}")
        # エラー時は通常の変換にフォールバック
        return title_to_kana(title)

def title_to_kana(title: str, use_ai: bool = False, api_key: str = None) -> str:
    """
    タイトル文字列をひらがなに変換する
    漢字・カタカナ・ローマ字・英語すべて対応
    
    Args:
        title: 元のタイトル（漢字・カタカナ・ひらがな・ローマ字・英語混在OK）
        use_ai: Trueの場合、AIを使用してより正確な変換を試みる
        api_key: AI APIキー（use_ai=Trueの場合に使用）
    
    Returns:
        ひらがなに変換された文字列（五十音順ソート用）
    """
    if not title:
        return ""
    
    # AI変換を試みる
    if use_ai:
        ai_result = title_to_kana_with_ai(title, api_key=api_key, provider="openai")
        if ai_result:  # AI変換が成功した場合
            return ai_result
    
    # Unicode正規化（全角・半角を統一）
    normalized = unicodedata.normalize("NFKC", title.strip())
    
    # 英字部分をローマ字変換テーブルでひらがなに変換
    def replace_romaji(match):
        romaji_text = match.group(0)
        return romaji_to_hiragana(romaji_text)
    
    # 英字部分をひらがなに変換
    normalized = re.sub(r'[a-zA-Z]+', replace_romaji, normalized)
    
    # pykakasiで残りの漢字・カタカナ→ひらがなに変換
    converter = get_kakasi()
    if converter is None:
        # pykakasiが使えない場合は変換済みの文字列を返す
        # スペースや記号を除去
        result = re.sub(r'[^\u3040-\u309F]', '', normalized)
        return result.strip().lower()
    
    try:
        # pykakasiで変換（結果はリストで返される）
        result = converter(normalized)
        # 各要素の'hira'（ひらがな）を結合
        kana = "".join([item.get('hira', item.get('orig', '')) for item in result])
        # スペースや記号を除去（ひらがなのみ残す）
        kana = re.sub(r'[^\u3040-\u309F]', '', kana)
        return kana.strip()
    except Exception as e:
        # エラー時は変換済みの文字列を返す
        print(f"かな変換エラー: {e}")
        # スペースや記号を除去
        result = re.sub(r'[^\u3040-\u309F]', '', normalized)
        return result.strip().lower()
