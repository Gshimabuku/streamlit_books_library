# AI搭載かな変換機能

このアプリケーションには、漫画タイトルをより正確なひらがなに変換するAI機能が搭載されています。

## 機能概要

- **自動変換**: タイトルかな欄を空欄で保存すると、自動的にひらがなが生成されます
- **AI変換**: OpenAI APIキーを設定すると、AIが漫画タイトルの正しい読み方を判断して変換します
- **フォールバック**: API未設定時は、pykakasiとローマ字変換テーブルを使用した通常変換が実行されます

## AI変換のメリット

### 通常変換の場合
- `ONE PIECE` → `おねぴえくえ`
- `進撃の巨人` → `しんげきのきょじん` ✓
- `Dragon Ball` → `どらごんばるる`

### AI変換の場合（GPT-4o-mini使用）
- `ONE PIECE` → `わんぴーす` ✓
- `進撃の巨人` → `しんげきのきょじん` ✓
- `Dragon Ball` → `どらごんぼーる` ✓
- `HUNTER×HUNTER` → `はんたーはんたー` ✓
- `僕のヒーローアカデミア` → `ぼくのひーろーあかでみあ` ✓

AIは文脈を理解し、漫画タイトルの正式な読み方を正確に判断します。

## セットアップ方法

### 1. OpenAI APIキーを取得

1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. アカウントを作成またはログイン
3. API Keys セクションで新しいAPIキーを作成
4. APIキーをコピー（`sk-...`で始まる文字列）

### 2. APIキーを設定

#### 方法A: secrets.tomlに設定（推奨）

`.streamlit/secrets.toml` ファイルに追加：

```toml
[notion]
api_key = "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
database_id = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

[openai]
api_key = "sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

#### 方法B: 環境変数に設定

```bash
export OPENAI_API_KEY="sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

### 3. 必要なパッケージをインストール

```bash
pip install -r requirements.txt
```

これで、`openai`ライブラリがインストールされます。

## 使用方法

### 新規漫画登録時

1. 「新しい漫画を登録」をクリック
2. タイトル欄に漫画タイトルを入力（例: `ONE PIECE`, `鬼滅の刃`, `Dragon Ball`）
3. **タイトルかな欄は空欄のまま**にする
4. その他の必須項目を入力
5. 「漫画を登録」をクリック

→ 保存時に自動でAIがタイトルを正確なひらがなに変換します

### 手動でかなを入力する場合

タイトルかな欄に直接ひらがなを入力すれば、その値が優先されます。

## 動作モード

```python
# AI APIキーあり → AI変換
"ONE PIECE" → AI判断 → "わんぴーす"

# AI APIキーなし → 通常変換
"ONE PIECE" → ローマ字変換 → "おねぴえくえ"
```

## コスト

- **モデル**: GPT-4o-mini
- **推定コスト**: タイトル1件あたり 約$0.0001（0.01円程度）
- **月間100件登録**: 約1円
- **非常に安価**: 実用上ほぼ無料

## トラブルシューティング

### AI変換が動作しない

1. APIキーが正しく設定されているか確認
   ```bash
   cat .streamlit/secrets.toml
   ```

2. openaiパッケージがインストールされているか確認
   ```bash
   pip list | grep openai
   ```

3. APIキーの権限を確認（OpenAI Platform）

### エラーが発生する

- **認証エラー**: APIキーが無効または期限切れ
- **レート制限**: 短時間に大量リクエストを送信している
- **残高不足**: OpenAIアカウントの残高を確認

どのエラーでも、**自動的に通常変換にフォールバック**されるため、登録は継続できます。

## Anthropic Claude使用（オプション）

OpenAIの代わりにAnthropic Claudeを使用することも可能です：

```toml
[anthropic]
api_key = "sk-ant-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

コード内で`provider="anthropic"`を指定して使用できます。

## まとめ

- ✅ APIキー設定で高精度AI変換が可能
- ✅ API未設定でも通常変換で動作
- ✅ コストは実質ほぼゼロ
- ✅ 手動入力も可能で柔軟
- ✅ 英語・日本語・ローマ字すべて対応

正確な五十音順ソートのため、AI変換の使用を推奨します！
