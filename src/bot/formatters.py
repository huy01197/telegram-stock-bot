"""
Module định dạng tin nhắn Telegram (Telegram Message Formatters).
Trình bày thông tin trực quan, chuyên nghiệp với emoji, cấu trúc thẻ và số liệu tài chính rõ ràng.
"""

# region 1. Thư viện & Định dạng Tin nhắn Chào mừng (/start)
from typing import Dict, Any, List


def format_welcome_message(bot_name: str = "Fintech AI Bot") -> str:
    """Định dạng tin nhắn chào mừng /start."""
    return (
        f"🤖 *CHÀO MỪNG BẠN ĐẾN VỚI {bot_name.upper()}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Trợ lý tư vấn và phát tín hiệu đầu tư chứng khoán Việt Nam chuẩn định lượng:\n"
        f"🔹 *Phân tích Kỹ thuật (TA)*: EMA 20/50, RSI 14, MACD, Nến Nhật\n"
        f"🔹 *Phân tích Cơ bản & Dòng tiền*: Tiêu chí CANSLIM (ROE > 15%, LN > 15%), Volume bùng nổ (>= 1.5x MA20)\n\n"
        f"📌 *DANH MỤC LỆNH ĐẦU TƯ CỐT LÕI:*\n"
        f"• `/signals` : Bảng tín hiệu Mua/Bán hôm nay\n"
        f"• `/check <MÃ>` : Kế hoạch vào lệnh (Entry, Target +14%, Stop Loss -7%, R:R=1:2)\n"
        f"• `/chart <MÃ>` : Xem đồ thị nến Nhật trực quan (EMA20/50, Volume, RSI)\n"
        f"• `/backtest <MÃ>` : Kiểm định hiệu năng thuật toán 3-6 tháng qua (Win Rate, MDD)\n"
        f"• `/top` : Top cổ phiếu tăng giá & thanh khoản bùng nổ phiên\n"
        f"• `/foreign` : Thống kê dòng tiền Khối ngoại Mua/Bán ròng\n"
        f"• `/filter` : Bộ lọc siêu cổ phiếu tăng trưởng CANSLIM\n"
        f"• `/market` : Tổng quan chỉ số VN-Index & thị trường chung\n"
        f"• `/sub <MÃ>` : Đăng ký nhận cảnh báo cho mã (vd: `/sub FPT`)\n"
        f"• `/unsub <MÃ>` : Hủy nhận cảnh báo (vd: `/unsub FPT`)\n"
        f"• `/watchlist` : Xem danh mục cổ phiếu đang đăng ký theo dõi\n\n"
        f"_Hãy chọn nút chức năng bên dưới hoặc gõ lệnh để bắt đầu!_"
    )
# endregion

# region 2. Định dạng Thẻ Phân tích Chi tiết (/check)
def format_analysis_card(analysis: Dict[str, Any]) -> str:
    """Định dạng thẻ phân tích chi tiết cho lệnh /check <MÃ>."""
    sym = analysis.get("symbol", "")
    sig = analysis.get("final_signal", "HOLD")
    score = analysis.get("composite_score", 50.0)
    p_info = analysis.get("price_info", {})
    close = p_info.get("close", 0.0)
    chg = p_info.get("change", 0.0)
    chg_pct = p_info.get("change_pct", 0.0)
    vol = p_info.get("volume", 0)

    # Emoji tín hiệu
    if "STRONG BUY" in sig:
        sig_emoji = "🟢🟢 *MUA MẠNH (STRONG BUY)*"
    elif "BUY" in sig:
        sig_emoji = "🟢 *KHUYẾN NGHỊ MUA (BUY)*"
    elif "SELL" in sig:
        sig_emoji = "🔴 *KHUYẾN NGHỊ BÁN (SELL)*"
    else:
        sig_emoji = "🟡 *THEO DÕI / NẮM GIỮ (HOLD)*"

    chg_str = f"+{chg:.2f} (+{chg_pct:.2f}%)" if chg > 0 else f"{chg:.2f} ({chg_pct:.2f}%)"
    trend_icon = "🔺" if chg > 0 else ("🔻" if chg < 0 else "▫️")

    # Chỉ số kỹ thuật
    ta_ind = analysis.get("ta_result", {}).get("indicators", {})
    ema_20 = ta_ind.get("ema_20", 0.0)
    ema_50 = ta_ind.get("ema_50", 0.0)
    rsi = ta_ind.get("rsi_14", 0.0)
    vol_ratio = ta_ind.get("vol_ratio", 1.0)
    macd_h = ta_ind.get("macd_hist", 0.0)

    # Chỉ số cơ bản FA
    fa = analysis.get("fa_metrics", {})
    roe = fa.get("roe", 0.0)
    pe = fa.get("pe", 0.0)
    pb = fa.get("pb", 0.0)
    growth = fa.get("profit_growth", 0.0)
    debt = fa.get("debt_to_equity", 0.0)

    # Mức giá khuyến nghị
    target = analysis.get("target_price", 0.0)
    stop_loss = analysis.get("stop_loss", 0.0)
    rr = analysis.get("risk_reward_ratio", 2.0)

    # Lý do then chốt
    ta_reasons = analysis.get("ta_result", {}).get("reasons", [])
    fa_reasons = analysis.get("fa_result", {}).get("reasons", [])
    all_reasons = ta_reasons[:2] + fa_reasons[:2]
    reasons_str = "\n".join([f"  ✓ {r}" for r in all_reasons]) if all_reasons else "  ✓ Đang trong vùng biến động hẹp"

    msg = (
        f"📊 *BÁO CÁO PHÂN TÍCH CỔ PHIẾU: {sym}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 *Thị giá*: `{close:,.1f}` {trend_icon} `{chg_str}` | Khối lượng: `{vol:,}`\n"
        f"🎯 *Tín hiệu tổng hợp*: {sig_emoji}\n"
        f"⭐ *Điểm đánh giá (0-100)*: *{score:.1f}/100*\n\n"
        f"📍 *KẾ HOẠCH GIAO DỊCH (R:R = 1:{rr:.0f})*:\n"
        f"• Giá vào lệnh (Entry): `{close:,.1f}`\n"
        f"• Giá mục tiêu (Target +14%): `{target:,.1f}`\n"
        f"• Giá cắt lỗ (Stop-Loss -7%): `{stop_loss:,.1f}`\n\n"
        f"📈 *CHỈ BÁO KỸ THUẬT (TA)*:\n"
        f"• EMA(20): `{ema_20:,.1f}` | EMA(50): `{ema_50:,.1f}`\n"
        f"• RSI(14): `{rsi:.1f}` {'(Quá mua)' if rsi > 70 else ('(Quá bán)' if rsi < 30 else '(Vùng tăng trưởng)')}\n"
        f"• MACD Hist: `{macd_h:+.3f}` | Đột biến Volume: `{vol_ratio:.2f}x`\n\n"
        f"🏢 *SỨC KHỎE DOANH NGHIỆP (FA)*:\n"
        f"• ROE: `{roe:.1f}%` (Ngưỡng > 15%)\n"
        f"• Tăng trưởng LNST: `{growth:+.1f}%` (Ngưỡng > 15%)\n"
        f"• Định giá: P/E = `{pe:.1f}` | P/B = `{pb:.1f}` | Nợ/VCSH = `{debt:.1f}`\n\n"
        f"💡 *LUẬN ĐIỂM ĐẦU TƯ:*\n{reasons_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ _Dữ liệu cập nhật thời gian thực từ VCI/SSI/CafeF_"
    )
    return msg
# endregion

# region 3. Định dạng Danh sách Tín hiệu Mua/Bán (/signals)
def format_signals_summary(scan_results: Dict[str, List[Dict[str, Any]]]) -> str:
    """Định dạng danh sách tín hiệu Mua/Bán hôm nay cho lệnh /signals."""
    buys = scan_results.get("buy", [])
    sells = scan_results.get("sell", [])
    holds = scan_results.get("hold", [])

    msg = (
        f"📢 *BẢNG TÍN HIỆU GIAO DỊCH HÔM NAY*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if buys:
        msg += f"🟢 *TÍN HIỆU MUA ({len(buys)} mã):*\n"
        for item in buys:
            sym = item["symbol"]
            score = item["composite_score"]
            close = item["price_info"]["close"]
            chg_pct = item["price_info"]["change_pct"]
            target = item["target_price"]
            msg += f"• *{sym}* | Giá: `{close:,.1f}` ({chg_pct:+.1f}%) | Target: `{target:,.1f}` | Điểm: *{score:.0f}*\n"
        msg += "\n"
    else:
        msg += "🟢 *TÍN HIỆU MUA*: Hiện chưa có mã nào thỏa mãn toàn bộ tiêu chí Breakout hôm nay.\n\n"

    if sells:
        msg += f"🔴 *TÍN HIỆU BÁN / CẢNH BÁO ({len(sells)} mã):*\n"
        for item in sells:
            sym = item["symbol"]
            close = item["price_info"]["close"]
            chg_pct = item["price_info"]["change_pct"]
            msg += f"• *{sym}* | Giá: `{close:,.1f}` ({chg_pct:+.1f}%) | Thủng hỗ trợ / Quá mua\n"
        msg += "\n"

    msg += (
        f"🟡 *THEO DÕI TÍCH LŨY*: {', '.join([h['symbol'] for h in holds[:8]])}...\n\n"
        f"💡 _Gõ `/check <MÃ>` để xem chi tiết điểm mua, cắt lỗ cụ thể từng mã._"
    )
    return msg
# endregion

# region 4. Định dạng Kết quả Bộ lọc Tăng trưởng (/filter)
def format_filter_results(candidates: List[Dict[str, Any]]) -> str:
    """Định dạng kết quả bộ lọc CANSLIM / Tăng trưởng cho lệnh /filter."""
    msg = (
        f"🏆 *BỘ LỌC CỔ PHIẾU TĂNG TRƯỞNG & DÒNG TIỀN*\n"
        f"_(Tiêu chí: ROE > 15%, Tăng trưởng LN > 15%, Bùng nổ khối lượng)_\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    if not candidates:
        msg += "Không có mã nào trong danh mục hiện tại thỏa mãn đủ các tiêu chí khắt khe."
        return msg

    for i, c in enumerate(candidates[:10], 1):
        sym = c["symbol"]
        fa = c.get("fa_metrics", {})
        roe = fa.get("roe", 0.0)
        growth = fa.get("profit_growth", 0.0)
        close = c.get("price_info", {}).get("close", 0.0)
        vol_ratio = c.get("ta_result", {}).get("indicators", {}).get("vol_ratio", 1.0)
        spike_str = "🔥 Volume bùng nổ" if vol_ratio >= 1.5 else "Đang tích lũy"

        msg += (
            f"*{i}. {sym}* — Thị giá: `{close:,.1f}`\n"
            f"   ▸ ROE: `{roe:.1f}%` | Tăng trưởng LN: `{growth:+.1f}%`\n"
            f"   ▸ Dòng tiền: `{vol_ratio:.1f}x MA20` ({spike_str})\n\n"
        )

    msg += "💡 _Gõ `/check <MÃ>` để xem chiến lược giải ngân chi tiết._"
    return msg
# endregion

# region 5. Định dạng Bản tin Thị trường VN-Index (/market)
def format_market_overview(market_info: Dict[str, Any]) -> str:
    """Định dạng bản tin thị trường /market."""
    close = market_info.get("close", 0.0)
    chg = market_info.get("change", 0.0)
    chg_pct = market_info.get("change_pct", 0.0)
    vol = market_info.get("volume", 0)
    time_str = market_info.get("time", "")

    trend_icon = "🟢 TĂNG ĐIỂM" if chg > 0 else ("🔴 GIẢM ĐIỂM" if chg < 0 else "🟡 ĐI NGANG")
    chg_str = f"+{chg:.2f} (+{chg_pct:.2f}%)" if chg > 0 else f"{chg:.2f} ({chg_pct:.2f}%)"

    return (
        f"🏛 *TỔNG QUAN THỊ TRƯỜNG CHỨNG KHOÁN (VN-INDEX)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Ngày cập nhật: `{time_str}`\n"
        f"📊 *Chỉ số VN-INDEX*: `{close:,.2f}` | {trend_icon}\n"
        f"📈 *Biến động*: `{chg_str}`\n"
        f"💰 *Khối lượng khớp lệnh*: `{vol:,}` cổ phiếu\n\n"
        f"📌 *NHẬN ĐỊNH TỪ HỆ THỐNG:*\n"
        f"• Xu hướng chung: {'Thị trường duy trì đà hồi phục tích cực, ưu tiên lựa chọn cổ phiếu dẫn dắt có dòng tiền.' if chg >= 0 else 'Thị trường gặp áp lực điều chỉnh ngắn hạn, khuyến nghị duy trì tỷ trọng an toàn và tuân thủ kỷ luật cắt lỗ -7%.'}\n\n"
        f"_Gõ `/signals` để xem các mã cổ phiếu ngược dòng thị trường hôm nay!_"
    )
# endregion

# region 6. Định dạng Báo cáo Kiểm thử Lịch sử (/backtest)
def format_backtest_report(symbol: str, res: Dict[str, Any], months: int = 6) -> str:
    """Định dạng kết quả kiểm thử chiến lược giao dịch trong quá khứ."""
    if "error" in res and res.get("total_trades", 0) == 0:
        return f"⚠️ *KIỂM THỬ {symbol.upper()}*: {res.get('error', 'Không đủ dữ liệu giao dịch để kiểm thử.')}"

    sym = symbol.upper()
    total_trades = res.get("total_trades", 0)
    win_rate = res.get("win_rate", 0.0)
    total_return = res.get("total_return", 0.0)
    mdd = res.get("max_drawdown", 0.0)
    profit_factor = res.get("profit_factor", 0.0)
    trades = res.get("trades", [])

    ret_icon = "🟢" if total_return >= 0 else "🔴"
    ret_str = f"+{total_return:.2f}%" if total_return >= 0 else f"{total_return:.2f}%"

    msg = (
        f"🧪 *BÁO CÁO KIỂM THỬ CHIẾN LƯỢC (BACKTEST): {sym}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ Thời gian kiểm định: *{months} tháng gần nhất*\n"
        f"🎯 Chiến lược: *Kỹ thuật EMA/RSI/MACD (Target +14%, Stop -7%)*\n\n"
        f"📊 *HIỆU NĂNG GIAO DỊCH:*\n"
        f"• Tổng số lệnh: *{total_trades} lệnh*\n"
        f"• Tỷ lệ thắng (Win Rate): *{win_rate:.1f}%*\n"
        f"• Tổng lợi nhuận: {ret_icon} *{ret_str}*\n"
        f"• Sụt giảm tối đa (MDD): *{mdd:.1f}%*\n"
        f"• Hệ số Profit Factor: *{profit_factor:.2f}*\n\n"
    )

    if trades:
        msg += "📝 *CHI TIẾT 3 LỆNH GẦN NHẤT:*\n"
        for t in trades[-3:]:
            pnl = t.get("pnl_pct", 0.0)
            icon = "✅" if pnl >= 0 else "❌"
            e_date = t.get("entry_date", "")
            x_date = t.get("exit_date", "")
            reason = t.get("exit_reason", "")
            msg += f"{icon} `{e_date}` ➜ `{x_date}` | PnL: *{pnl:+.1f}%* ({reason})\n"
        msg += "\n"

    msg += f"💡 _Gõ `/chart {sym}` để xem đồ thị nến hoặc `/check {sym}` để xem kế hoạch hiện tại._"
    return msg
# endregion

# region 7. Định dạng Bảng Xếp Hạng Phiên (/top) & Dòng Tiền Khối Ngoại (/foreign)
def format_top_movers(data: Dict[str, List[Dict[str, Any]]]) -> str:
    """Định dạng kết quả Top cổ phiếu tăng/giảm và thanh khoản trong phiên."""
    gainers = data.get("gainers", [])
    losers = data.get("losers", [])
    vol_leaders = data.get("volume_leaders", [])

    msg = (
        f"🚀 *BẢNG XẾP HẠNG THỊ TRƯỜNG PHIÊN HÔM NAY*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if gainers:
        msg += "🟢 *TOP TĂNG GIÁ MẠNH NHẤT:*\n"
        for g in gainers[:5]:
            msg += f"• *{g['symbol']}*: `{g['close']:,.0f}` ({g['change_pct']:+.2f}%) | Vol: `{g['volume']:,}`\n"
        msg += "\n"

    if losers:
        msg += "🔴 *TOP GIẢM GIÁ MẠNH NHẤT:*\n"
        for l in losers[:5]:
            msg += f"• *{l['symbol']}*: `{l['close']:,.0f}` ({l['change_pct']:+.2f}%) | Vol: `{l['volume']:,}`\n"
        msg += "\n"

    if vol_leaders:
        msg += "🔥 *TOP THANH KHOẢN / KHỐI LƯỢNG LỚN NHẤT:*\n"
        for v in vol_leaders[:5]:
            msg += f"• *{v['symbol']}*: `{v['volume']:,}` CP | Giá: `{v['close']:,.0f}` ({v['change_pct']:+.2f}%)\n"
        msg += "\n"

    msg += "💡 _Gõ `/chart <MÃ>` hoặc `/check <MÃ>` để phân tích chi tiết mã dẫn đầu._"
    return msg


def format_foreign_flow(data: Dict[str, Any]) -> str:
    """Định dạng thống kê giao dịch Mua/Bán ròng Khối ngoại."""
    top_buy = data.get("top_net_buy", [])
    top_sell = data.get("top_net_sell", [])
    total_buy = data.get("total_buy_vol", 0)
    total_sell = data.get("total_sell_vol", 0)
    net_total = data.get("total_net_vol", 0)

    net_icon = "🟢 MUA RÒNG" if net_total >= 0 else "🔴 BÁN RÒNG"
    net_str = f"+{net_total:,}" if net_total >= 0 else f"{net_total:,}"

    msg = (
        f"🌐 *THỐNG KÊ DÒNG TIỀN KHỐI NGOẠI (FOREIGN FLOW)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Toàn thị trường*: Khối ngoại {net_icon} `{net_str}` CP\n"
        f"• Tổng mua: `{total_buy:,}` CP\n"
        f"• Tổng bán: `{total_sell:,}` CP\n\n"
    )

    if top_buy:
        msg += "🟢 *TOP CỔ PHIẾU KHỐI NGOẠI MUA RÒNG:*\n"
        for b in top_buy[:5]:
            msg += f"• *{b['symbol']}*: Mua ròng `+{b['net_vol']:,}` CP (Mua: `{b['buy_vol']:,}` | Bán: `{b['sell_vol']:,}`)\n"
        msg += "\n"

    if top_sell:
        msg += "🔴 *TOP CỔ PHIẾU KHỐI NGOẠI BÁN RÒNG:*\n"
        for s in top_sell[:5]:
            msg += f"• *{s['symbol']}*: Bán ròng `{s['net_vol']:,}` CP (Bán: `{s['sell_vol']:,}` | Mua: `{s['buy_vol']:,}`)\n"
        msg += "\n"

    msg += "💡 _Theo dõi hành vi khối ngoại giúp nhận biết cổ phiếu đang được định chế lớn gom hàng._"
    return msg


def format_watchlist(symbols: List[str]) -> str:
    """Định dạng danh sách mã đang theo dõi."""
    if not symbols:
        return (
            "⭐ *DANH MỤC ĐĂNG KÝ CỦA BẠN ĐANG TRỐNG*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👉 Để đăng ký nhận cảnh báo, hãy gõ: `/sub <MÃ>` (ví dụ: `/sub FPT` hoặc `/sub SSI`)\n"
            "Hệ thống sẽ tự động giám sát và thông báo khi cổ phiếu có điểm nổ vol hoặc điểm mua mới!"
        )

    sym_str = ", ".join([f"`{s}`" for s in symbols])
    return (
        f"⭐ *DANH MỤC CỔ PHIẾU ĐÃ ĐĂNG KÝ ({len(symbols)} MÃ)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 Danh sách: {sym_str}\n\n"
        f"📌 *HƯỚNG DẪN QUẢN LÝ:*\n"
        f"• Đăng ký mã: `/sub <MÃ>`\n"
        f"• Hủy đăng ký: `/unsub <MÃ>`\n"
        f"• Xem đồ thị: `/chart <MÃ>`\n"
        f"• Kiểm tra kế hoạch: `/check <MÃ>`"
    )
# endregion
