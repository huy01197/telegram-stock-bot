"""
Chiến lược 2: Phân tích Cơ bản kết hợp Dòng tiền (Value/Growth + Momentum)
Mô hình định lượng:
1. Bộ lọc cơ bản (FA Filter):
   - Chỉ lọc các cổ phiếu có tăng trưởng doanh thu/lợi nhuận > 15% (dữ liệu CafeF/SSI/VNF)
   - ROE > 15% (hiệu quả sinh lời trên vốn chủ sở hữu vượt trội)
   - Đòn bẩy nợ/VCSH an toàn (< 2.0)
2. Kích hoạt tín hiệu Mua (Momentum Trigger):
   - Khối lượng bùng nổ đột biến: Volume >= 1.5 lần trung bình 20 phiên (Vol Ratio >= 1.5)
   - Giá tăng tốt (nến xanh, đóng cửa cao hơn EMA 20 và vượt nền tích lũy)
3. Tín hiệu Bán / Quản trị rủi ro:
   - Volume bán tháo lớn cắt thủng hỗ trợ
   - Cắt lỗ nghiêm ngặt 7%, chốt lời 14 - 20%.
"""

# region 1. Thư viện & Cấu hình Chiến lược Tăng trưởng
from typing import Dict, Any
import pandas as pd
from src.strategy.indicators import add_all_indicators
import config
# endregion

# region 2. Lớp GrowthMomentumStrategy & Logic Đánh giá Tín hiệu
class GrowthMomentumStrategy:
    def __init__(self, fa_config: Dict[str, Any] = None, ta_config: Dict[str, Any] = None):
        self.fa_config = fa_config or config.FA_CONFIG
        self.ta_config = ta_config or config.TA_CONFIG

    def evaluate(self, df: pd.DataFrame, fa_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Đánh giá chiến lược kết hợp FA + Dòng tiền bùng nổ.
        """
        if df.empty or len(df) < 25:
            return {
                "strategy": "Value/Growth + Momentum (CANSLIM)",
                "signal": "HOLD",
                "score": 50.0,
                "reasons": ["Dữ liệu nến giá chưa đủ để phân tích dòng tiền"],
                "entry_price": 0.0,
                "target_price": 0.0,
                "stop_loss": 0.0,
                "fa_pass": False,
                "volume_spike": False
            }

        df_ind = add_all_indicators(df)
        curr = df_ind.iloc[-1]
        prev = df_ind.iloc[-2]

        close = float(curr["close"])
        open_price = float(curr["open"])
        vol_ratio = float(curr["vol_ratio"]) if pd.notnull(curr["vol_ratio"]) else 1.0
        ema_20 = float(curr["ema_20"])

        # 1. Đánh giá tiêu chí cơ bản (FA Filter)
        roe = float(fa_metrics.get("roe", 0.0))
        profit_growth = float(fa_metrics.get("profit_growth", 0.0))
        debt_to_equity = float(fa_metrics.get("debt_to_equity", 1.0))
        pe = float(fa_metrics.get("pe", 0.0))

        min_roe = self.fa_config.get("min_roe", 15.0)
        min_growth = self.fa_config.get("min_profit_growth", 15.0)
        max_de = self.fa_config.get("max_debt_to_equity", 2.0)

        roe_pass = roe >= min_roe
        growth_pass = profit_growth >= min_growth
        debt_pass = debt_to_equity <= max_de
        fa_pass = roe_pass and (growth_pass or roe >= 20.0) and debt_pass

        # 2. Đánh giá tiêu chí dòng tiền (Momentum / Volume Spike)
        spike_ratio_threshold = self.ta_config.get("volume_spike_ratio", 1.5)
        volume_spike = vol_ratio >= spike_ratio_threshold
        price_up = close >= open_price and close >= prev["close"]
        breakout = close > ema_20 and price_up

        reasons = []
        score = 50.0

        if fa_pass:
            reasons.append(f"Cơ bản xuất sắc: ROE đạt {roe:.1f}% (ngưỡng > {min_roe}%), Tăng trưởng LN {profit_growth:.1f}%")
            score += 25.0
        else:
            reasons.append(f"Chỉ số cơ bản: ROE {roe:.1f}%, Tăng trưởng LN {profit_growth:.1f}%")

        if volume_spike and price_up:
            reasons.append(f"Bùng nổ khối lượng vượt trội: Gấp {vol_ratio:.1f}x trung bình 20 phiên (ngưỡng > {spike_ratio_threshold}x)")
            score += 25.0
            if breakout:
                reasons.append(f"Giá bứt phá mạnh mẽ vượt đường trung bình EMA 20 ({close:.1f} > {ema_20:.1f})")
                score += 10.0

        # Tổng hợp Tín hiệu
        if fa_pass and volume_spike and breakout:
            signal = "BUY"
            reasons.insert(0, "HỘI TỤ ĐIỂM MUA BÙNG NỔ: Cổ phiếu tăng trưởng đón dòng tiền lớn gia nhập")
        elif not price_up and volume_spike and close < ema_20:
            signal = "SELL"
            reasons.insert(0, "ÁP LỰC BÁN THÁO: Khối lượng lớn đột biến nhưng giá giảm gãy hỗ trợ")
            score -= 30.0
        elif fa_pass:
            signal = "HOLD"
            reasons.append("Cổ phiếu tốt đang tích lũy, tiếp tục theo dõi chờ phiên bùng nổ dòng tiền")
        else:
            signal = "HOLD"
            reasons.append("Chưa thỏa mãn đồng thời bộ lọc Cơ bản và Dòng tiền")

        stop_loss_pct = config.RISK_CONFIG.get("stop_loss_pct", 0.07)
        take_profit_pct = config.RISK_CONFIG.get("take_profit_pct", 0.14)

        entry_price = close
        stop_loss = round(close * (1.0 - stop_loss_pct), 2)
        target_price = round(close * (1.0 + take_profit_pct), 2)

        return {
            "strategy": "Value/Growth + Momentum (CANSLIM)",
            "signal": signal,
            "score": min(max(round(score, 1), 0.0), 100.0),
            "reasons": reasons,
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "fa_pass": fa_pass,
            "volume_spike": volume_spike,
            "metrics": {
                "roe": roe,
                "profit_growth": profit_growth,
                "pe": pe,
                "vol_ratio": vol_ratio,
                "close": close
            }
        }
# endregion
