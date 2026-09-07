"""
Bộ máy điều phối chiến lược (Strategy Engine).
Tổng hợp phân tích từ cả 2 trường phái:
- Chiến lược 1: Phân tích Kỹ thuật (TA - Golden Cross, RSI, MACD)
- Chiến lược 2: Cơ bản & Dòng tiền bùng nổ (FA + Momentum Spike)
Đưa ra khuyến nghị cuối cùng (Consensus Action: BUY/SELL/HOLD), chấm điểm và thiết lập mức giá mục tiêu / cắt lỗ.
"""

# region 1. Thư viện & Khởi tạo Engine
import logging
from typing import List, Dict, Any, Optional
from src.data.data_loader import DataLoader
from src.data.financial_loader import FinancialLoader
from src.strategy.technical import TechnicalStrategy
from src.strategy.growth_flow import GrowthMomentumStrategy
import config

logger = logging.getLogger(__name__)


class StrategyEngine:
    def __init__(
        self,
        data_loader: Optional[DataLoader] = None,
        financial_loader: Optional[FinancialLoader] = None
    ):
        self.data_loader = data_loader or DataLoader()
        self.financial_loader = financial_loader or FinancialLoader()
        self.ta_strategy = TechnicalStrategy()
        self.growth_strategy = GrowthMomentumStrategy()
# endregion

# region 2. Phân tích Chi tiết Từng Mã & Chấm điểm Tổng hợp
    def analyze_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Phân tích toàn diện một mã cổ phiếu:
        - Tải lịch sử giá OHLCV và chỉ số BCTC
        - Thực thi Chiến lược 1 (TA) và Chiến lược 2 (FA + Momentum)
        - Tính điểm tổng hợp (Composite Score) và khuyến nghị chung.
        """
        symbol = symbol.upper().strip()
        df = self.data_loader.get_history(symbol=symbol, days=180)
        fa_metrics = self.financial_loader.get_financial_metrics(symbol=symbol)

        if df.empty or len(df) < 25:
            return {
                "symbol": symbol,
                "final_signal": "HOLD",
                "composite_score": 50.0,
                "summary": f"Chưa đủ dữ liệu thị trường cho mã {symbol}",
                "ta_result": {},
                "fa_result": {},
                "price_info": {"close": 0.0, "change": 0.0, "change_pct": 0.0}
            }

        # Đánh giá 2 chiến lược
        ta_eval = self.ta_strategy.evaluate(df)
        fa_eval = self.growth_strategy.evaluate(df, fa_metrics)

        # Lấy thông tin giá mới nhất
        latest_price = self.data_loader.get_latest_price(symbol)

        # Tính điểm tổng hợp (Composite Score: Trọng số 50% TA + 50% FA & Dòng tiền)
        score_ta = ta_eval.get("score", 50.0)
        score_fa = fa_eval.get("score", 50.0)
        composite_score = round(0.5 * score_ta + 0.5 * score_fa, 1)

        # Quyết định tín hiệu khuyến nghị chung
        sig_ta = ta_eval.get("signal", "HOLD")
        sig_fa = fa_eval.get("signal", "HOLD")

        if sig_ta == "BUY" and sig_fa == "BUY":
            final_signal = "STRONG BUY"
            recommendation_text = "MUA MẠNH: Hội tụ đồng thuận cả Xu hướng Kỹ thuật và Bùng nổ Dòng tiền Cơ bản!"
        elif sig_ta == "BUY" or sig_fa == "BUY":
            final_signal = "BUY"
            lead_strat = "Kỹ thuật (TA)" if sig_ta == "BUY" else "Cơ bản & Dòng tiền (CANSLIM)"
            recommendation_text = f"MUA: Xuất hiện tín hiệu khả quan từ chiến lược {lead_strat}."
        elif sig_ta == "SELL" or sig_fa == "SELL":
            final_signal = "SELL"
            recommendation_text = "BÁN / HẠ TỶ TRỌNG: Chỉ báo kỹ thuật suy yếu hoặc chạm ngưỡng rủi ro."
        else:
            final_signal = "HOLD"
            recommendation_text = "NẮM GIỮ / QUAN SÁT: Cổ phiếu đang trong pha tích lũy, chờ đợi xác nhận."

        close = latest_price.get("close", 0.0)
        stop_loss_pct = config.RISK_CONFIG.get("stop_loss_pct", 0.07)
        take_profit_pct = config.RISK_CONFIG.get("take_profit_pct", 0.14)

        return {
            "symbol": symbol,
            "final_signal": final_signal,
            "composite_score": composite_score,
            "recommendation_text": recommendation_text,
            "price_info": latest_price,
            "entry_price": close,
            "target_price": round(close * (1.0 + take_profit_pct), 2),
            "stop_loss": round(close * (1.0 - stop_loss_pct), 2),
            "risk_reward_ratio": round(take_profit_pct / stop_loss_pct, 1),
            "ta_result": ta_eval,
            "fa_result": fa_eval,
            "fa_metrics": fa_metrics
        }
# endregion

# region 3. Quét Danh mục Tín hiệu Mua/Bán Toàn Thị trường
    def scan_watchlist(self, symbols: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Quét danh sách theo dõi để tìm các tín hiệu Mua/Bán/Nắm giữ.
        Trả về: {"buy": [...], "sell": [...], "hold": [...]}
        """
        watchlist = symbols or config.DEFAULT_WATCHLIST
        results = {"buy": [], "sell": [], "hold": []}

        for sym in watchlist:
            try:
                analysis = self.analyze_symbol(sym)
                sig = analysis["final_signal"]
                if "BUY" in sig:
                    results["buy"].append(analysis)
                elif "SELL" in sig:
                    results["sell"].append(analysis)
                else:
                    results["hold"].append(analysis)
            except Exception as e:
                logger.error(f"Lỗi khi quét mã {sym}: {e}")

        # Sắp xếp danh sách Mua theo điểm số cao nhất giảm dần
        results["buy"].sort(key=lambda x: x["composite_score"], reverse=True)
        results["sell"].sort(key=lambda x: x["composite_score"])
        results["hold"].sort(key=lambda x: x["composite_score"], reverse=True)

        return results
# endregion

# region 4. Bộ lọc Cổ phiếu Tăng trưởng & Dòng tiền
    def filter_growth_momentum(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Lọc các cổ phiếu thỏa mãn tiêu chí Cơ bản tăng trưởng (ROE > 15%, LN > 15%)."""
        watchlist = symbols or config.DEFAULT_WATCHLIST
        candidates = []

        for sym in watchlist:
            try:
                analysis = self.analyze_symbol(sym)
                fa_pass = analysis.get("fa_result", {}).get("fa_pass", False)
                if fa_pass or analysis.get("fa_metrics", {}).get("roe", 0) >= 15.0:
                    candidates.append(analysis)
            except Exception as e:
                logger.error(f"Lỗi lọc mã {sym}: {e}")

        candidates.sort(key=lambda x: x.get("fa_metrics", {}).get("roe", 0), reverse=True)
        return candidates
# endregion
