"""Database Service - Wrapper around existing database module"""

from pathlib import Path
from typing import Optional

from ..config import settings

# Import existing database module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from pokergo_downloader.core.database import Database

# Singleton instance
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """Get database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(settings.database_path)
    return _db_instance


def reset_db():
    """Reset database instance (for testing)"""
    global _db_instance
    _db_instance = None
