"""
Module Backtesting: Kiểm định hiệu năng chiến lược đầu tư trong quá khứ (3 - 6 tháng).
Tính toán các chỉ số tài chính tiêu chuẩn:
- Total Return (%)
- Win Rate (%)
- Profit Factor (Hệ số Lợi nhuận / Rủi ro)
- Maximum Drawdown (MDD - Mức sụt giảm tài sản tối đa)
- Số lệnh giao dịch thực hiện & Chi tiết lịch sử lệnh
"""

# region 1. Thư viện & Khởi tạo Backtest Engine
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.strategy.indicators import add_all_indicators
import config


class BacktestEngine:
    def __init__(
        self,
        stop_loss_pct: float = 0.07,
        take_profit_pct: float = 0.14,
        slippage_fee_pct: float = 0.003  # 0.3% phí giao dịch + thuế khứ hồi
    ):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.slippage_fee_pct = slippage_fee_pct
# endregion

# region 2. Vòng lặp Mô phỏng Giao dịch Lịch sử
    def run(self, df: pd.DataFrame, strategy_type: str = "TA") -> Dict[str, Any]:
        """
        Chạy backtest trên dữ liệu OHLCV lịch sử.
        strategy_type: 'TA' (Kỹ thuật EMA/RSI/MACD) hoặc 'GROWTH' (Dòng tiền bùng nổ)
        """
        if df.empty or len(df) < 50:
            return {
                "error": "Không đủ dữ liệu để backtest (yêu cầu >= 50 phiên)",
                "total_trades": 0,
                "win_rate": 0.0,
                "total_return": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0,
                "trades": []
            }

        df_ind = add_all_indicators(df)
        trades = []
        in_position = False
        entry_price = 0.0
        entry_date = None

        equity_curve = [100.0]  # Khởi đầu với số vốn cơ số 100

        # Quét từng phiên từ phiên thứ 50
        for i in range(50, len(df_ind)):
            row = df_ind.iloc[i]
            prev = df_ind.iloc[i - 1]
            date_str = str(row["time"])[:10]
            close = float(row["close"])
            high = float(row["high"])
            low = float(row["low"])

            if in_position:
                # Kiểm tra chạm ngưỡng Cắt lỗ (Stop Loss -7%)
                stop_price = entry_price * (1.0 - self.stop_loss_pct)
                # Kiểm tra chạm ngưỡng Chốt lời (Take Profit +14%)
                target_price = entry_price * (1.0 + self.take_profit_pct)

                exit_price = None
                exit_reason = ""

                if low <= stop_price:
                    exit_price = stop_price
                    exit_reason = "Hit Stop Loss (-7.0%)"
                elif high >= target_price:
                    exit_price = target_price
                    exit_reason = "Hit Take Profit (+14.0%)"
                else:
                    # Kiểm tra tín hiệu thoát vị thế kỹ thuật
                    rsi = float(row["rsi_14"])
                    prev_rsi = float(prev["rsi_14"])
                    ema_50 = float(row["ema_50"])

                    if prev_rsi >= 70.0 and rsi < prev_rsi:
                        exit_price = close
                        exit_reason = f"RSI Overbought Pullback ({rsi:.1f})"
                    elif close < ema_50:
                        exit_price = close
                        exit_reason = "Close Below Support (EMA 50)"

                # Thực hiện chốt lệnh nếu có lý do thoát
                if exit_price is not None:
                    gross_pnl = (exit_price - entry_price) / entry_price
                    net_pnl = gross_pnl - self.slippage_fee_pct
                    pnl_pct = round(net_pnl * 100, 2)

                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": date_str,
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "pnl_pct": pnl_pct,
                        "exit_reason": exit_reason,
                        "win": pnl_pct > 0
                    })

                    new_equity = equity_curve[-1] * (1.0 + net_pnl)
                    equity_curve.append(new_equity)
                    in_position = False

            else:
                # Tìm tín hiệu Mua vào
                ema_20 = float(row["ema_20"])
                ema_50 = float(row["ema_50"])
                prev_ema_20 = float(prev["ema_20"])
                prev_ema_50 = float(prev["ema_50"])
                rsi = float(row["rsi_14"])
                vol_ratio = float(row["vol_ratio"]) if pd.notnull(row["vol_ratio"]) else 1.0

                buy_signal = False
                if strategy_type == "TA":
                    ema_cross = (prev_ema_20 <= prev_ema_50) and (ema_20 > ema_50)
                    rsi_ok = 50.0 < rsi < 70.0
                    if ema_cross and rsi_ok:
                        buy_signal = True
                    elif ema_20 > ema_50 and close > ema_50 and prev_ema_20 <= prev_ema_50 * 1.01 and rsi > 52.0:
                        buy_signal = True
                else:  # GROWTH / MOMENTUM
                    if vol_ratio >= 1.5 and close > ema_20 and close > float(row["open"]):
                        buy_signal = True

                if buy_signal:
                    in_position = True
                    entry_price = close
                    entry_date = date_str

        # Nếu còn lệnh mở ở phiên cuối cùng
        if in_position:
            last_close = float(df_ind.iloc[-1]["close"])
            gross_pnl = (last_close - entry_price) / entry_price
            net_pnl = gross_pnl - self.slippage_fee_pct
            pnl_pct = round(net_pnl * 100, 2)
            trades.append({
                "entry_date": entry_date,
                "exit_date": str(df_ind.iloc[-1]["time"])[:10],
                "entry_price": round(entry_price, 2),
                "exit_price": round(last_close, 2),
                "pnl_pct": pnl_pct,
                "exit_reason": "Open Position (Mark to Market)",
                "win": pnl_pct > 0
            })
            equity_curve.append(equity_curve[-1] * (1.0 + net_pnl))
# endregion

# region 3. Thống kê & Tính toán Chỉ số Tài chính (Win Rate, Drawdown, Profit Factor)
        total_trades = len(trades)
        if total_trades > 0:
            win_trades = sum(1 for t in trades if t["win"])
            loss_trades = total_trades - win_trades
            win_rate = round((win_trades / total_trades) * 100, 2)

            gains = [t["pnl_pct"] for t in trades if t["pnl_pct"] > 0]
            losses = [abs(t["pnl_pct"]) for t in trades if t["pnl_pct"] < 0]

            total_gain = sum(gains)
            total_loss = sum(losses)
            profit_factor = round(total_gain / total_loss, 2) if total_loss > 0 else (99.0 if total_gain > 0 else 0.0)

            total_return = round(((equity_curve[-1] - 100.0) / 100.0) * 100, 2)

            peak = equity_curve[0]
            max_dd = 0.0
            for val in equity_curve:
                if val > peak:
                    peak = val
                dd = (peak - val) / peak
                if dd > max_dd:
                    max_dd = dd
            max_drawdown = round(max_dd * 100, 2)
        else:
            win_rate = 0.0
            total_return = 0.0
            profit_factor = 0.0
            max_drawdown = 0.0
            win_trades = 0
            loss_trades = 0

        return {
            "strategy": strategy_type,
            "total_trades": total_trades,
            "win_trades": win_trades,
            "loss_trades": loss_trades,
            "win_rate": win_rate,
            "total_return": total_return,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "trades": trades
        }
# endregion
