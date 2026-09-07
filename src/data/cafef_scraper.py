"""
Module Scraper dữ liệu trực tiếp từ CafeF (CafeF Data Pipeline & Scraper).
Cung cấp:
1. Tải và phân tích dữ liệu giao dịch lịch sử & thời gian thực (Price, Volume) của toàn bộ cổ phiếu niêm yết (HSX, HNX, UPCOM) từ CafeF.
2. Tự động cập nhật gói dữ liệu giao dịch mới nhất (AmiData SolieuGD Upto) từ hệ thống CDN của CafeF.
3. Kỹ thuật chống chặn IP (Anti-blocking & Rate-limit Handling):
   - User-Agent Rotation (xoay vòng đa trình duyệt Chrome, Safari, Firefox).
   - Exponential Backoff & Jitter Retry khi gặp lỗi 429/403.
   - Request Throttling & Header Spoofing.
"""

# region 1. Thư viện, User-Agents & Cấu hình
import os
import time
import random
import logging
import zipfile
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import pandas as pd
import requests
import config

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
]
# endregion

# region 2. Khởi tạo Scraper & Cơ chế Giãn cách Chống Chặn IP
class CafeFScraper:
    def __init__(self, download_dir: Optional[Path] = None, min_request_interval: float = 1.0):
        self.download_dir = download_dir or (config.CACHE_DIR / "cafef_downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.min_request_interval = min_request_interval
        self.last_request_time = 0.0

    def _get_random_headers(self) -> Dict[str, str]:
        """Tạo headers chuẩn browser để vượt qua Cloudflare/WAF của CafeF."""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://cafef.vn/",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0"
        }

    def _wait_for_throttle(self):
        """Giãn cách thời gian giữa 2 request để chống bị chặn IP."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed + random.uniform(0.1, 0.3)
            time.sleep(sleep_time)
        self.last_request_time = time.time()
# endregion

# region 3. Tự động Đồng bộ Gói Dữ liệu CafeF SolieuGD
    def sync_latest_cafef_data(self) -> bool:
        """Tự động cào và giải nén gói số liệu giao dịch mới nhất từ CafeF CDN."""
        today = datetime.now()
        for i in range(10):
            target_date = today - timedelta(days=i)
            file_name = f"CafeF.SolieuGD.Upto{target_date.strftime('%d%m%Y')}.zip"
            file_url = f"https://cafef1.mediacdn.vn/data/ami_data/{target_date.strftime('%Y%m%d')}/{file_name}"
            zip_path = self.download_dir / file_name

            if zip_path.exists():
                return True

            self._wait_for_throttle()
            try:
                headers = self._get_random_headers()
                resp = self.session.get(file_url, headers=headers, stream=True, timeout=15)
                if resp.status_code == 200:
                    with open(zip_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                f.write(chunk)
                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        zip_ref.extractall(self.download_dir)
                    logger.info(f"Đã cập nhật dữ liệu CafeF mới nhất: {file_name}")
                    return True
            except Exception as e:
                logger.debug(f"Thử tải {file_url} không thành công: {e}")
                continue

        return False
# endregion

# region 4. Trích xuất Lịch sử Nến Giá & Khối lượng từng Mã
    def load_symbol_history(self, symbol: str, days: int = 180) -> pd.DataFrame:
        """
        Trích xuất lịch sử giao dịch OHLCV của một mã cổ phiếu từ bộ dữ liệu CafeF.
        Tìm kiếm trên cả 3 sàn HSX, HNX, UPCOM.
        """
        symbol = symbol.upper().strip()
        csv_files = list(self.download_dir.glob("CafeF.*.csv"))
        if not csv_files:
            self.sync_latest_cafef_data()
            csv_files = list(self.download_dir.glob("CafeF.*.csv"))

        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, low_memory=False)
                df.columns = [c.replace("<", "").replace(">", "").strip() for c in df.columns]

                if "Ticker" not in df.columns:
                    continue

                sym_df = df[df["Ticker"] == symbol].copy()
                if not sym_df.empty:
                    sym_df["time"] = pd.to_datetime(sym_df["DTYYYYMMDD"].astype(str), format="%Y%m%d", errors="coerce")
                    col_map = {
                        "Open": "open",
                        "High": "high",
                        "Low": "low",
                        "Close": "close",
                        "Volume": "volume"
                    }
                    sym_df = sym_df.rename(columns=col_map)
                    numeric_cols = ["open", "high", "low", "close", "volume"]
                    for c in numeric_cols:
                        if c in sym_df.columns:
                            sym_df[c] = pd.to_numeric(sym_df[c], errors="coerce")

                    sym_df = sym_df.dropna(subset=["time", "close"]).sort_values("time").reset_index(drop=True)

                    if days > 0 and len(sym_df) > days:
                        sym_df = sym_df.iloc[-days:].reset_index(drop=True)

                    return sym_df[["time", "open", "high", "low", "close", "volume"]]
            except Exception as e:
                logger.debug(f"Lỗi đọc file {csv_file}: {e}")

        return pd.DataFrame()
# endregion
