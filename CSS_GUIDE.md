# Books Library - CSS管理ガイド

## 概要

このプロジェクトでは、StreamlitアプリケーションのCSSスタイルを外部ファイルで管理しています。これにより、保守性と再利用性が向上し、コードの可読性も改善されます。

## CSSファイル構造

```
static/
├── styles.css        # メインスタイル（全ページ共通）
├── add_book.css      # 新規登録ページ専用
└── book_detail.css   # 詳細ページ専用
```

## CSSファイルの詳細

### `styles.css` - メインスタイル
- 新規登録ボタンのスタイル
- 本のカード表示
- アコーディオンボタン
- 雑誌名ヘッダー
- モバイル対応レスポンシブデザイン
- 詳細画面のボタン配置

### `add_book.css` - 新規登録ページ
- フォーム関連のスタイル
- アップロード機能のスタイル
- 登録成功メッセージのスタイル

### `book_detail.css` - 詳細ページ
- 詳細ページのレイアウト
- ステータスバッジ（完結/連載中）
- 情報セクション
- レスポンシブデザイン

## CSSローダーの使用方法

### 基本的な使い方

```python
from utils.css_loader import load_custom_styles, load_page_styles

# アプリケーション全体のスタイルを読み込み
load_custom_styles()

# 特定のページ用スタイルを追加読み込み
load_page_styles("add_book")  # add_book.cssを読み込み
load_page_styles("book_detail")  # book_detail.cssを読み込み
```

### app.pyでの実装例

```python
def main():
    # カスタムCSSを読み込み
    load_custom_styles()
    
    st.title("📚 Books Library")
    
    if st.session_state.page == "add_book":
        load_page_styles("add_book")
        show_add_book()
    elif st.session_state.page == "book_detail":
        load_page_styles("book_detail")
        show_book_detail()
```

## 新しいCSSファイルの追加

1. `static/`ディレクトリに新しいCSSファイルを作成
2. `load_page_styles()`を使用してCSSファイルを読み込み

例：
```python
# static/new_page.css を作成後
load_page_styles("new_page")
```

## CSSクラス名の規則

### 命名規則
- ケバブケース（kebab-case）を使用：`book-card`, `detail-buttons-container`
- 機能や場所を表す名前：`add-book-button`, `magazine-name-header`
- レスポンシブ用プレフィックス：`mobile-book-image`

### よく使用されるクラス
- `.book-card` - 本の表示カード
- `.add-book-button` - 新規登録ボタン
- `.detail-buttons-container` - 詳細ページのボタン配置
- `.magazine-name-header` - 雑誌名のヘッダー
- `.mobile-*` - モバイル専用スタイル

## レスポンシブデザイン

### ブレークポイント
- モバイル：`@media (max-width: 768px)`
- デスクトップ：`@media (min-width: 769px)`

### モバイル対応
- フレックスボックスを活用した横並び表示
- ボタンサイズの調整
- フォントサイズの最適化

## トラブルシューティング

### CSSが適用されない場合
1. ファイルパスの確認：`static/`ディレクトリ内に正しく配置されているか
2. ファイル名の確認：拡張子`.css`が正しく付いているか
3. 読み込み順序の確認：`load_custom_styles()`が最初に呼ばれているか

### CSS優先度の問題
- Streamlitの既存スタイルを上書きするため、`!important`を使用
- より具体的なセレクタを使用

## 今後の拡張

### 新機能追加時
1. 新しいCSSファイルの作成
2. `load_page_styles()`での読み込み
3. 必要に応じてメインスタイルの更新

### パフォーマンス向上
- CSS圧縮の導入
- 未使用スタイルの除去
- キャッシュ機能の追加

## メリット

### 保守性
- スタイルの一元管理
- コードとスタイルの分離
- 変更時の影響範囲の明確化

### 再利用性
- 複数ページでの共通スタイル利用
- テーマの一貫性維持
- 開発効率の向上

### 可読性
- Pythonコードからスタイル定義の除去
- CSS専用エディタでのシンタックスハイライト
- バージョン管理の改善