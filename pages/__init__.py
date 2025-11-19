"""
Pages module: Screen-specific logic for each page
"""

from .home import show_books_home
from .detail import show_book_detail
from .add import show_add_book
from .edit import show_edit_book

__all__ = [
    'show_books_home',
    'show_book_detail',
    'show_add_book',
    'show_edit_book',
]
