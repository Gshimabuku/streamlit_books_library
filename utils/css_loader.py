"""
CSS読み込み用のユーティリティ関数
"""
import streamlit as st
import os

def load_css(file_name):
    """
    CSSファイルを読み込んでStreamlitに適用する
    
    Args:
        file_name (str): CSSファイル名（staticディレクトリ内）
    """
    css_file_path = os.path.join("static", file_name)
    
    try:
        with open(css_file_path, "r", encoding="utf-8") as f:
            css = f.read()
        
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        
    except FileNotFoundError:
        st.error(f"CSSファイルが見つかりません: {css_file_path}")
    except Exception as e:
        st.error(f"CSSファイルの読み込みでエラーが発生しました: {str(e)}")

def load_custom_styles():
    """
    アプリケーション全体で使用するカスタムスタイルを読み込む
    """
    load_css("styles.css")
    # load_css("default.css")

def load_page_styles(page_name):
    """
    特定のページ用のCSSを読み込む
    
    Args:
        page_name (str): ページ名（add_book, book_detail等）
    """
    css_filename = f"{page_name}.css"
    load_css(css_filename)