"""
Storage package for data management.
Provides in-memory and SQLite storage for question-answer pairs.
"""

from storage.memory import MemoryStorage
from storage.sqlite import SQLiteStorage

__all__ = ['MemoryStorage', 'SQLiteStorage']
