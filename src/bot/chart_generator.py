"""
Module sinh đồ thị nến Nhật (Candlestick Chart Generator) phục vụ phân tích kỹ thuật.
Thiết kế theo phong cách Dark Mode hiện đại (chuẩn TradingView / Bloomberg):
- Panel 1: Nến Nhật OHLC + Đường EMA 20 (vàng) + Đường EMA 50 (xanh dương)
- Panel 2: Cột khối lượng (Volume) + Đường Volume MA20 (cam)
- Panel 3: Chỉ báo RSI 14 kèm dải Quá mua (70) và Quá bán (30)
Xuất trực tiếp ra io.BytesIO (Memory Buffer) để gửi nhanh qua Telegram mà không cần lưu rác ổ đĩa.
"""

# region 1. Thư viện & Cấu hình Matplotlib Backend
import io
import logging
from typing import Optional
import pandas as pd
import numpy as np
import matplotlib
# Thiết lập backend không tương tác (Headless) để chạy mượt mà trên Server/Bot
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from src.strategy.indicators import add_all_indicators

logger = logging.getLogger(__name__)
# endregion

# region 2. Hàm Dựng Đồ thị Nến Nhật Đa tầng
def generate_stock_chart(df: pd.DataFrame, symbol: str, days: int = 75) -> Optional[io.BytesIO]:
    """
    Tạo hình ảnh đồ thị phân tích kỹ thuật 3 tầng cho mã cổ phiếu.
    Trả về: io.BytesIO buffer chứa file ảnh PNG hoặc None nếu có lỗi.
    """
    if df.empty or len(df) < 20:
        logger.warning(f"Không đủ dữ liệu vẽ nến cho {symbol} (cần >= 20 phiên)")
        return None

    try:
        # Chuẩn hóa chỉ báo kỹ thuật
        df_ind = add_all_indicators(df)
        df_plot = df_ind.tail(days).copy().reset_index(drop=True)

        if len(df_plot) < 10:
            df_plot = df_ind.copy().reset_index(drop=True)

        # Đổi định dạng thời gian
        df_plot["time"] = pd.to_datetime(df_plot["time"])
        n_bars = len(df_plot)

        # Bảng màu Dark Mode chuyên nghiệp
        bg_color = "#131722"         # Màu nền chính (TradingView Dark)
        grid_color = "#2a2e39"       # Màu lưới kẻ
        text_color = "#d1d4dc"       # Màu chữ
        candle_up = "#089981"        # Nến xanh tăng giá (Bullish Green)
        candle_down = "#f23645"      # Nến đỏ giảm giá (Bearish Red)
        ema20_color = "#f59e0b"      # EMA 20 vàng cam
        ema50_color = "#3b82f6"      # EMA 50 xanh lam
        rsi_color = "#a855f7"        # RSI tím mộng mơ
        vol_ma_color = "#ec4899"     # Volume MA hồng đậm

        # Khởi tạo Figure 3 trục Subplots
        fig, (ax_price, ax_vol, ax_rsi) = plt.subplots(
            nrows=3,
            ncols=1,
            figsize=(11, 7.5),
            sharex=True,
            gridspec_kw={"height_ratios": [5, 1.8, 1.8], "hspace": 0.08},
            facecolor=bg_color
        )

        for ax in (ax_price, ax_vol, ax_rsi):
            ax.set_facecolor(bg_color)
            ax.tick_params(colors=text_color, labelsize=9)
            ax.grid(True, color=grid_color, linestyle="--", linewidth=0.5, alpha=0.7)
            for spine in ax.spines.values():
                spine.set_color(grid_color)

        # -------------------------------------------------------------
        # TẦNG 1: BIỂU ĐỒ NẾN NHẬT (CANDLESTICKS) & ĐƯỜNG EMA 20 / EMA 50
        # -------------------------------------------------------------
        width = 0.65
        indices = np.arange(n_bars)
        opens = df_plot["open"].values
        highs = df_plot["high"].values
        lows = df_plot["low"].values
        closes = df_plot["close"].values

        for i in range(n_bars):
            o, h, l, c = opens[i], highs[i], lows[i], closes[i]
            color = candle_up if c >= o else candle_down

            # Vẽ râu nến (Shadow/Wick)
            ax_price.plot([i, i], [l, h], color=color, linewidth=1.1, solid_capstyle="round")

            # Vẽ thân nến (Real Body)
            body_bottom = min(o, c)
            body_height = max(abs(c - o), (h - l) * 0.02 if h != l else 0.1)
            rect = Rectangle(
                (i - width / 2, body_bottom),
                width,
                body_height,
                facecolor=color,
                edgecolor=color,
                linewidth=0.5
            )
            ax_price.add_patch(rect)

        # Vẽ đường EMA 20 và EMA 50
        if "ema_20" in df_plot.columns:
            ax_price.plot(indices, df_plot["ema_20"].values, color=ema20_color, label="EMA 20", linewidth=1.5)
        if "ema_50" in df_plot.columns:
            ax_price.plot(indices, df_plot["ema_50"].values, color=ema50_color, label="EMA 50", linewidth=1.5)

        # Đánh dấu giá hiện tại
        latest_c = closes[-1]
        prev_c = closes[-2] if n_bars > 1 else latest_c
        change_pct = ((latest_c - prev_c) / prev_c) * 100 if prev_c > 0 else 0
        status_color = candle_up if change_pct >= 0 else candle_down
        latest_date = df_plot["time"].iloc[-1].strftime("%d/%m/%Y")

        ax_price.set_title(
            f"[{symbol.upper()}] - PHÂN TÍCH KỸ THUẬT (Ngày: {latest_date}) | Giá: {latest_c:,.0f} ({change_pct:+.2f}%)",
            color="#ffffff",
            fontsize=11,
            fontweight="bold",
            pad=10,
            loc="left"
        )
        ax_price.legend(loc="upper left", facecolor="#1e222d", edgecolor=grid_color, labelcolor=text_color, fontsize=9)
        ax_price.set_ylabel("Giá (VNĐ)", color=text_color, fontsize=9)

        # Vẽ vạch giá hiện tại bên mép phải
        ax_price.axhline(latest_c, color=status_color, linestyle=":", linewidth=1.0, alpha=0.8)

        # -------------------------------------------------------------
        # TẦNG 2: KHỐI LƯỢNG GIAO DỊCH (VOLUME & VOLUME MA20)
        # -------------------------------------------------------------
        volumes = df_plot["volume"].values
        vol_colors = [candle_up if c >= o else candle_down for o, c in zip(opens, closes)]
        ax_vol.bar(indices, volumes, color=vol_colors, width=width, alpha=0.85, label="Khối lượng")

        if "vol_ma_20" in df_plot.columns:
            ax_vol.plot(indices, df_plot["vol_ma_20"].values, color=vol_ma_color, label="MA20 Khối lượng", linewidth=1.3)

        ax_vol.legend(loc="upper left", facecolor="#1e222d", edgecolor=grid_color, labelcolor=text_color, fontsize=8)
        ax_vol.set_ylabel("Khối lượng", color=text_color, fontsize=9)

        # -------------------------------------------------------------
        # TẦNG 3: CHỈ SỐ SỨC MẠNH TƯƠNG ĐỐI (RSI 14)
        # -------------------------------------------------------------
        if "rsi_14" in df_plot.columns:
            rsi_vals = df_plot["rsi_14"].values
            ax_rsi.plot(indices, rsi_vals, color=rsi_color, label="RSI (14)", linewidth=1.4)
            ax_rsi.axhline(70, color=candle_down, linestyle="--", linewidth=0.9, alpha=0.7)
            ax_rsi.axhline(30, color=candle_up, linestyle="--", linewidth=0.9, alpha=0.7)
            ax_rsi.fill_between(indices, 30, 70, color="#6b21a8", alpha=0.12)

            latest_rsi = rsi_vals[-1]
            ax_rsi.text(
                n_bars - 0.5, latest_rsi, f" {latest_rsi:.1f}",
                color=rsi_color, va="center", fontsize=8, fontweight="bold"
            )

        ax_rsi.set_ylim(10, 90)
        ax_rsi.set_yticks([30, 50, 70])
        ax_rsi.legend(loc="upper left", facecolor="#1e222d", edgecolor=grid_color, labelcolor=text_color, fontsize=8)
        ax_rsi.set_ylabel("RSI", color=text_color, fontsize=9)

        # -------------------------------------------------------------
        # ĐỊNH DẠNG TRỤC THỜI GIAN (X-AXIS)
        # -------------------------------------------------------------
        step = max(2, n_bars // 7)
        tick_indices = list(range(0, n_bars, step))
        if (n_bars - 1) not in tick_indices:
            if len(tick_indices) > 1 and ((n_bars - 1) - tick_indices[-1]) < (step * 0.65):
                tick_indices[-1] = n_bars - 1
            else:
                tick_indices.append(n_bars - 1)

        tick_labels = [df_plot["time"].iloc[idx].strftime("%d/%m") for idx in tick_indices]
        ax_rsi.set_xticks(tick_indices)
        ax_rsi.set_xticklabels(tick_labels, rotation=0, fontsize=9)
        ax_rsi.set_xlim(-0.8, n_bars + 2.0)

        # Lưu ảnh ra BytesIO buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=140, bbox_inches="tight", facecolor=bg_color)
        plt.close(fig)
        buf.seek(0)
        return buf

    except Exception as e:
        logger.error(f"Lỗi khi sinh đồ thị nến cho {symbol}: {e}")
        plt.close("all")
        return None
# endregion
