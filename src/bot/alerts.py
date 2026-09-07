"""
Module quản lý cảnh báo tự động (Alert Manager).
Lưu trữ đăng ký nhận thông báo của người dùng và hỗ trợ kiểm tra phát hiện tín hiệu thời gian thực.
"""

# region 1. Thư viện & Cấu hình Cơ sở Dữ liệu Cảnh báo
import sqlite3
import time
import logging
from typing import List, Dict
from pathlib import Path
import config

logger = logging.getLogger(__name__)
# endregion

# region 2. Lớp AlertManager & Khởi tạo Bảng
class AlertManager:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.CACHE_DB_PATH
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(str(self.db_path), timeout=10.0)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_alerts (
                        chat_id INTEGER,
                        symbol TEXT,
                        created_at REAL,
                        PRIMARY KEY (chat_id, symbol)
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Lỗi khởi tạo bảng user_alerts: {e}")
# endregion

# region 3. Đăng ký & Hủy Đăng ký Nhận Cảnh báo
    def add_alert(self, chat_id: int, symbol: str) -> bool:
        """Đăng ký nhận cảnh báo cho một mã cổ phiếu."""
        symbol = symbol.upper().strip()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO user_alerts (chat_id, symbol, created_at)
                    VALUES (?, ?, ?)
                """, (chat_id, symbol, time.time()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Lỗi thêm alert {symbol} cho {chat_id}: {e}")
            return False

    def remove_alert(self, chat_id: int, symbol: str) -> bool:
        """Hủy đăng ký nhận cảnh báo cho một mã."""
        symbol = symbol.upper().strip()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_alerts WHERE chat_id = ? AND symbol = ?", (chat_id, symbol))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Lỗi xóa alert {symbol} cho {chat_id}: {e}")
            return False

    def get_user_alerts(self, chat_id: int) -> List[str]:
        """Lấy danh sách các mã người dùng đang theo dõi cảnh báo."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT symbol FROM user_alerts WHERE chat_id = ? ORDER BY symbol ASC", (chat_id,))
                rows = cursor.fetchall()
                return [r[0] for r in rows]
        except Exception as e:
            logger.error(f"Lỗi lấy alerts của {chat_id}: {e}")
            return []
# endregion

# region 4. Truy vấn Danh sách Người theo dõi theo Mã
    def get_all_subscribers_by_symbol(self) -> Dict[str, List[int]]:
        """Lấy danh sách mã và các chat_id tương ứng để gửi thông báo định kỳ."""
        result: Dict[str, List[int]] = {}
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT chat_id, symbol FROM user_alerts")
                rows = cursor.fetchall()
                for chat_id, symbol in rows:
                    if symbol not in result:
                        result[symbol] = []
                    result[symbol].append(chat_id)
        except Exception as e:
            logger.error(f"Lỗi truy vấn all subscribers: {e}")
        return result
# endregion
