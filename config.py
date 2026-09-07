"""
Module cấu hình tập trung cho toàn bộ hệ thống Telegram Bot Đầu Tư Chứng Khoán.
Bao gồm: API Token, danh sách mã cổ phiếu theo dõi, các tham số chỉ báo kỹ thuật,
tiêu chí lọc báo cáo tài chính và ngưỡng quản trị rủi ro.
"""

# region 1. Thư viện & Nạp Biến Môi Trường
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
# endregion

# region 2. Cấu hình Telegram Bot & Bộ nhớ đệm (Cache)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

CACHE_DIR = BASE_DIR / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_DB_PATH = CACHE_DIR / "market_cache.db"

# Thời gian sống của cache (giây)
PRICE_CACHE_TTL = int(os.getenv("PRICE_CACHE_TTL", "900"))          # 15 phút cho giá giao dịch
FINANCIAL_CACHE_TTL = int(os.getenv("FINANCIAL_CACHE_TTL", "86400")) # 24 giờ cho BCTC

# Nguồn dữ liệu & môi trường chạy
DEFAULT_DATA_SOURCE = os.getenv("DEFAULT_DATA_SOURCE", "DIRECT")
ENV = os.getenv("ENV", "development")
ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL", "300"))
# endregion

# region 3. Danh sách Mã Cổ phiếu Theo dõi Mặc định
DEFAULT_WATCHLIST = [
    "FPT", "SSI", "HPG", "VNM", "MWG", "TCB", "MBB", "VCB", "STB", 
    "MSN", "VHM", "VIC", "DGC", "VCI", "VND", "GAS", "PLX", "PVD",
    "FRT", "KDH", "REE", "PNJ"
]
# endregion

# region 4. Tham số Phân tích Kỹ thuật (TA Config)
TA_CONFIG = {
    "ema_fast": 20,              # Chu kỳ EMA nhanh
    "ema_slow": 50,              # Chu kỳ EMA chậm
    "rsi_period": 14,            # Chu kỳ RSI
    "rsi_bullish_min": 50.0,     # Ngưỡng RSI tối thiểu để xác nhận xu hướng tăng
    "rsi_overbought": 70.0,      # Ngưỡng RSI quá mua (bắt đầu cảnh báo rủi ro chốt lời)
    "rsi_oversold": 30.0,        # Ngưỡng RSI quá bán (cơ hội phục hồi)
    "volume_ma_period": 20,      # Chu kỳ trung bình khối lượng
    "volume_spike_ratio": 1.5,   # Tỷ lệ bùng nổ khối lượng (>= 1.5 lần trung bình 20 phiên)
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
}
# endregion

# region 5. Tham số Phân tích Cơ bản (FA Config)
FA_CONFIG = {
    "min_roe": 15.0,             # ROE tối thiểu 15%
    "min_profit_growth": 15.0,   # Tăng trưởng lợi nhuận tối thiểu 15%
    "min_revenue_growth": 10.0,  # Tăng trưởng doanh thu tối thiểu 10%
    "max_debt_to_equity": 2.0,   # Tỷ lệ Nợ vay/VCSH tối đa
    "min_eps": 1500,             # Thu nhập trên mỗi cổ phần (EPS) tối thiểu
}
# endregion

# region 6. Quy chuẩn Quản trị Rủi ro (Risk Management)
RISK_CONFIG = {
    "stop_loss_pct": 0.07,       # Cắt lỗ ở mức -7% từ điểm vào lệnh (chuẩn CANSLIM)
    "take_profit_pct": 0.14,     # Chốt lời mục tiêu ở mức +14% (R:R = 1:2)
    "trailing_stop_pct": 0.05,   # Trailing stop bảo toàn lợi nhuận
}
# endregion
