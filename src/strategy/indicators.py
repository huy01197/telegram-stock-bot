"""
Module tính toán các chỉ báo kỹ thuật (Technical Indicators).
Bao gồm:
- EMA (Exponential Moving Average)
- SMA (Simple Moving Average)
- RSI (Relative Strength Index theo phương pháp Wilder)
- MACD (Moving Average Convergence Divergence)
- Volume MA & Volume Spike Ratio
- ATR (Average True Range) phục vụ tính toán cắt lỗ/chốt lời động
"""

# region 1. Thư viện Toán học
import pandas as pd
import numpy as np
# endregion

# region 2. Đường Trung bình Động (EMA & SMA)
def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    """Tính đường Trung bình Động Lũy thừa (EMA)."""
    return series.ewm(span=span, adjust=False).mean()


def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """Tính đường Trung bình Động Giản đơn (SMA)."""
    return series.rolling(window=window, min_periods=1).mean()
# endregion

# region 3. Chỉ số Sức mạnh Tương đối (RSI Wilder)
def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Tính chỉ số Sức mạnh Tương đối (RSI) theo công thức chuẩn Wilder's RSI.
    RS = Average Gain / Average Loss
    RSI = 100 - (100 / (1 + RS))
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)
# endregion

# region 4. Đường Phân kỳ Hội tụ Trung bình Động (MACD)
def calculate_macd(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> pd.DataFrame:
    """
    Tính toán chỉ báo MACD:
    - MACD Line = EMA(fast) - EMA(slow)
    - Signal Line = EMA(signal, MACD Line)
    - MACD Histogram = MACD Line - Signal Line
    """
    ema_fast = calculate_ema(series, span=fast_period)
    ema_slow = calculate_ema(series, span=slow_period)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, span=signal_period)
    histogram = macd_line - signal_line

    return pd.DataFrame({
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    })
# endregion

# region 5. Biên độ Dao động Thực tế (ATR)
def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Tính độ biến động trung bình thực tế (Average True Range - ATR)."""
    high = df["high"]
    low = df["low"]
    close_prev = df["close"].shift(1)

    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    return atr.fillna(0.0)
# endregion

# region 6. Hàm Tổng hợp Toàn bộ Chỉ báo (Pipeline Transformer)
def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hàm tổng hợp: Bổ sung toàn bộ các chỉ báo kỹ thuật vào DataFrame giá.
    Cột thêm vào:
    - ema_20, ema_50
    - rsi_14
    - macd, macd_signal, macd_hist
    - vol_ma_20, vol_ratio
    - atr_14
    """
    if df.empty or len(df) < 5:
        return df

    res = df.copy()
    close = res["close"]
    vol = res["volume"]

    # EMA
    res["ema_20"] = calculate_ema(close, span=20)
    res["ema_50"] = calculate_ema(close, span=50)

    # RSI
    res["rsi_14"] = calculate_rsi(close, period=14)

    # MACD
    macd_df = calculate_macd(close, fast_period=12, slow_period=26, signal_period=9)
    res["macd"] = macd_df["macd"]
    res["macd_signal"] = macd_df["signal"]
    res["macd_hist"] = macd_df["histogram"]

    # Khối lượng
    res["vol_ma_20"] = calculate_sma(vol, window=20)
    res["vol_ratio"] = (vol / res["vol_ma_20"].replace(0, np.nan)).round(2)

    # ATR
    res["atr_14"] = calculate_atr(res, period=14)

    return res
# endregion
