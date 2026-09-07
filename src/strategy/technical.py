"""
Chiến lược 1: Phân tích Kỹ thuật (Technical Analysis - TA)
Mô hình kỹ thuật:
- Tín hiệu MUA (BUY):
  + Đường EMA 20 cắt lên (Golden Cross) hoặc nằm trên EMA 50
  + Chỉ số RSI(14) > 50 (xác nhận xung lực mua mạnh) và chưa vào vùng quá mua cực đại (< 70)
  + Giá đóng cửa duy trì trên đường hỗ trợ EMA 50
  + Xác nhận thêm từ MACD Histogram > 0
- Tín hiệu BÁN (SELL):
  + Giá thủng đường hỗ trợ then chốt (EMA 50 hoặc giảm quá ngưỡng Stop-loss 7%)
  + RSI vượt lên vùng quá mua (> 70) và có dấu hiệu quay đầu giảm
  + Đường EMA 20 cắt xuống dưới EMA 50 (Death Cross)
- Trạng thái NẮM GIỮ / THEO DÕI (HOLD):
  + Các điều kiện chưa hội tụ đủ hoặc thị trường đang sideway tích lũy.
"""

# region 1. Thư viện & Cấu hình Chiến lược Kỹ thuật
from typing import Dict, Any
import pandas as pd
from src.strategy.indicators import add_all_indicators
import config
# endregion

# region 2. Lớp TechnicalStrategy & Logic Đánh giá Tín hiệu
class TechnicalStrategy:
    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or config.TA_CONFIG

    def evaluate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Đánh giá tín hiệu kỹ thuật cho chuỗi dữ liệu nến giá.
        """
        if df.empty or len(df) < 50:
            return {
                "signal": "HOLD",
                "score": 50.0,
                "reasons": ["Dữ liệu lịch sử chưa đủ (yêu cầu tối thiểu 50 phiên)"],
                "entry_price": 0.0,
                "target_price": 0.0,
                "stop_loss": 0.0,
                "indicators": {}
            }

        df_ind = add_all_indicators(df)
        curr = df_ind.iloc[-1]
        prev = df_ind.iloc[-2]

        close = float(curr["close"])
        ema_20 = float(curr["ema_20"])
        ema_50 = float(curr["ema_50"])
        prev_ema_20 = float(prev["ema_20"])
        prev_ema_50 = float(prev["ema_50"])

        rsi = float(curr["rsi_14"])
        prev_rsi = float(prev["rsi_14"])

        macd_hist = float(curr["macd_hist"])
        vol_ratio = float(curr["vol_ratio"]) if pd.notnull(curr["vol_ratio"]) else 1.0

        reasons = []
        score = 50.0

        # 1. Kiểm tra cắt lên (Golden Cross) hoặc xu hướng tăng của EMA
        ema_crossed_up = (prev_ema_20 <= prev_ema_50) and (ema_20 > ema_50)
        ema_bullish = ema_20 > ema_50 and close > ema_50

        # 2. Kiểm tra cắt xuống (Death Cross) hoặc thủng hỗ trợ
        ema_crossed_down = (prev_ema_20 >= prev_ema_50) and (ema_20 < ema_50)
        price_below_support = close < ema_50

        # 3. Kiểm tra hành vi RSI
        rsi_bullish = (rsi > self.params.get("rsi_bullish_min", 50.0)) and (rsi < self.params.get("rsi_overbought", 70.0))
        rsi_overbought_turning = (prev_rsi >= 70.0) and (rsi < prev_rsi)

        # 4. Kiểm tra MACD
        macd_bullish = macd_hist > 0

        # Tổng hợp Tín hiệu Mua
        if ema_crossed_up and rsi_bullish:
            reasons.append("EMA 20 vừa cắt lên EMA 50 (Golden Cross chuẩn)")
            reasons.append(f"RSI({rsi:.1f}) > 50 xác nhận xung lực dòng tiền tích cực")
            score += 35.0
            if macd_bullish:
                reasons.append("MACD Histogram dương hỗ trợ đà tăng")
                score += 10.0
            signal = "BUY"
        elif ema_bullish and rsi_bullish and (rsi > prev_rsi or macd_bullish):
            reasons.append("Xu hướng tăng trung hạn vững chắc (Giá > EMA 20 > EMA 50)")
            reasons.append(f"RSI đang mạnh ({rsi:.1f}) đồng thuận với xu hướng tăng")
            score += 25.0
            if macd_bullish:
                score += 10.0
            signal = "BUY" if score >= 75.0 else "HOLD"
        # Tổng hợp Tín hiệu Bán
        elif rsi_overbought_turning:
            reasons.append(f"RSI chạm vùng quá mua ({prev_rsi:.1f}) và quay đầu giảm ({rsi:.1f})")
            score -= 30.0
            signal = "SELL"
        elif price_below_support or ema_crossed_down:
            reasons.append("Giá đóng cửa gãy thủng đường hỗ trợ EMA 50")
            if ema_crossed_down:
                reasons.append("EMA 20 cắt xuống EMA 50 (Death Cross cảnh báo rủi ro)")
            score -= 35.0
            signal = "SELL"
        else:
            signal = "HOLD"
            reasons.append("Chỉ báo kỹ thuật đang ở vùng tích lũy, chưa có điểm phá vỡ (Breakout)")

        # Tính toán mức giá Entry, Target (chốt lời), Stop Loss (cắt lỗ)
        stop_loss_pct = config.RISK_CONFIG.get("stop_loss_pct", 0.07)
        take_profit_pct = config.RISK_CONFIG.get("take_profit_pct", 0.14)

        entry_price = close
        stop_loss = round(close * (1.0 - stop_loss_pct), 2)
        target_price = round(close * (1.0 + take_profit_pct), 2)

        return {
            "strategy": "Technical Analysis (EMA + RSI + MACD)",
            "signal": signal,
            "score": min(max(round(score, 1), 0.0), 100.0),
            "reasons": reasons,
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "indicators": {
                "close": close,
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "rsi_14": round(rsi, 2),
                "macd_hist": round(macd_hist, 3),
                "vol_ratio": round(vol_ratio, 2)
            }
        }
# endregion
