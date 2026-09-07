"""
Module quản lý bộ nhớ đệm (Cache Manager) sử dụng SQLite.
Tối ưu tốc độ phản hồi cho Telegram Bot (< 0.5s) và bảo vệ hệ thống không bị rate limit/chặn IP.
"""

# region 1. Thư viện & Cấu hình Logging
import sqlite3
import time
import json
import logging
import io
import pandas as pd
from typing import Optional, Any
from pathlib import Path
import config

logger = logging.getLogger(__name__)
# endregion

# region 2. Khởi tạo Cơ sở Dữ liệu Cache SQLite
class CacheManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.CACHE_DB_PATH
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(str(self.db_path), timeout=10.0)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS kv_cache (
                        key TEXT PRIMARY KEY,
                        value_json TEXT,
                        updated_at REAL,
                        ttl REAL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS df_cache (
                        key TEXT PRIMARY KEY,
                        df_json TEXT,
                        updated_at REAL,
                        ttl REAL
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Cache DB: {e}")
# endregion

# region 3. Các hàm Đọc/Ghi Key-Value (JSON Cache)
    def get(self, key: str) -> Optional[Any]:
        """Lấy giá trị JSON từ cache nếu còn hạn (TTL)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value_json, updated_at, ttl FROM kv_cache WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    value_json, updated_at, ttl = row
                    if time.time() - updated_at <= ttl:
                        return json.loads(value_json)
                    else:
                        cursor.execute("DELETE FROM kv_cache WHERE key = ?", (key,))
                        conn.commit()
        except Exception as e:
            logger.warning(f"Lỗi đọc cache key '{key}': {e}")
        return None

    def set(self, key: str, value: Any, ttl: float = 900):
        """Lưu giá trị vào cache với thời hạn TTL (giây)."""
        try:
            val_str = json.dumps(value, ensure_ascii=False)
            now = time.time()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO kv_cache (key, value_json, updated_at, ttl)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value_json=excluded.value_json,
                        updated_at=excluded.updated_at,
                        ttl=excluded.ttl
                """, (key, val_str, now, ttl))
                conn.commit()
        except Exception as e:
            logger.warning(f"Lỗi ghi cache key '{key}': {e}")
# endregion

# region 4. Các hàm Đọc/Ghi DataFrame (Table Cache)
    def get_df(self, key: str) -> Optional[pd.DataFrame]:
        """Lấy DataFrame từ cache nếu còn hạn."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT df_json, updated_at, ttl FROM df_cache WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    df_json, updated_at, ttl = row
                    if time.time() - updated_at <= ttl:
                        return pd.read_json(io.StringIO(df_json), orient="split")
                    else:
                        cursor.execute("DELETE FROM df_cache WHERE key = ?", (key,))
                        conn.commit()
        except Exception as e:
            logger.warning(f"Lỗi đọc DataFrame cache key '{key}': {e}")
        return None

    def set_df(self, key: str, df: pd.DataFrame, ttl: float = 900):
        """Lưu DataFrame vào cache."""
        try:
            if df is None or df.empty:
                return
            df_json = df.to_json(orient="split", date_format="iso")
            now = time.time()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO df_cache (key, df_json, updated_at, ttl)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        df_json=excluded.df_json,
                        updated_at=excluded.updated_at,
                        ttl=excluded.ttl
                """, (key, df_json, now, ttl))
                conn.commit()
        except Exception as e:
            logger.warning(f"Lỗi ghi DataFrame cache key '{key}': {e}")
# endregion

# region 5. Dọn dẹp & Xóa Cache
    def clear(self):
        """Xóa toàn bộ cache."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM kv_cache")
                cursor.execute("DELETE FROM df_cache")
                conn.commit()
        except Exception as e:
            logger.warning(f"Lỗi xóa cache: {e}")
# endregion
