"""
Chương trình chính khởi chạy Telegram Bot Đầu Tư Chứng Khoán (Fintech Bot).
Thiết kế tối ưu: Chỉ cần bấm nút PLAY (Run) trong VS Code là toàn bộ hệ thống
tự động kết nối, in thông tin trạng thái trực quan và hoạt động ngay lập tức mà không cần gõ lệnh.
"""

# region 1. Thư viện & Cấu hình Logging
import sys
import argparse
import logging
import requests
from src.strategy.strategy_engine import StrategyEngine
from src.backtest.engine import BacktestEngine
from src.bot.alerts import AlertManager
from src.bot.chart_generator import generate_stock_chart
from src.bot.formatters import (
    format_welcome_message,
    format_analysis_card,
    format_signals_summary,
    format_filter_results,
    format_market_overview,
    format_backtest_report,
    format_top_movers,
    format_foreign_flow,
    format_watchlist,
)
import config

# Cấu hình logging ngắn gọn, chuyên nghiệp
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
# Tắt log HTTP spam từ httpx/telegram để Terminal hiển thị sạch sẽ
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.INFO)
# endregion

# region 2. Chế độ Trình diễn Tương tác (Interactive Demo CLI)
def run_interactive_demo():
    """Chế độ mô phỏng tương tác dành cho kiểm thử dòng lệnh."""
    print("\n" + "=" * 75)
    print("🚀 KHỞI ĐỘNG CHẾ ĐỘ TRÌNH DIỄN (INTERACTIVE DEMO CLI) - FINTECH BOT")
    print("=" * 75)
    print(format_welcome_message())
    print("-" * 75)

    engine = StrategyEngine()
    backtest_engine = BacktestEngine()
    alert_mgr = AlertManager()

    while True:
        try:
            cmd_input = input("\n👉 Nhập lệnh (/signals, /check FPT, /chart FPT, /backtest FPT, /top, /foreign, /filter, /market, /sub FPT, /unsub FPT, 'exit'): ").strip()
            if not cmd_input:
                continue

            if cmd_input.lower() in ["exit", "quit", "q"]:
                print("👋 Đã thoát khỏi chương trình.")
                break

            parts = cmd_input.split()
            cmd = parts[0].lower()
            arg = parts[1].upper() if len(parts) > 1 else ""

            if cmd in ["/start", "/help"]:
                print("\n" + format_welcome_message())

            elif cmd in ["/signals", "/today"]:
                print("\n⏳ Đang quét tín hiệu thị trường hôm nay...")
                scan_res = engine.scan_watchlist(["FPT", "SSI", "HPG", "VNM", "MWG", "TCB", "MBB", "VCI"])
                print("\n" + format_signals_summary(scan_res))

            elif cmd in ["/check", "/lookup"]:
                symbol = arg or "FPT"
                print(f"\n⏳ Đang phân tích mã {symbol}...")
                analysis = engine.analyze_symbol(symbol)
                print("\n" + format_analysis_card(analysis))

            elif cmd == "/chart":
                symbol = arg or "FPT"
                print(f"\n⏳ Đang dựng đồ thị nến kỹ thuật cho {symbol}...")
                df = engine.data_loader.get_history(symbol=symbol, days=90)
                buf = generate_stock_chart(df, symbol=symbol, days=60)
                if buf:
                    print(f"✅ Đã tạo thành công ảnh đồ thị nến Nhật ({len(buf.getvalue()):,} bytes). Trên Telegram ảnh này sẽ được gửi trực tiếp!")
                else:
                    print(f"❌ Không thể tạo đồ thị cho {symbol}.")

            elif cmd == "/backtest":
                symbol = arg or "FPT"
                print(f"\n⏳ Đang kiểm định chiến lược cho {symbol} trong 6 tháng qua...")
                df = engine.data_loader.get_history(symbol=symbol, days=210)
                res = backtest_engine.run(df)
                print("\n" + format_backtest_report(symbol, res, months=6))

            elif cmd == "/top":
                print("\n⏳ Đang lấy bảng xếp hạng phiên hôm nay...")
                data = engine.data_loader.get_market_movers()
                print("\n" + format_top_movers(data))

            elif cmd == "/foreign":
                print("\n⏳ Đang thống kê dòng tiền Khối ngoại...")
                data = engine.data_loader.get_foreign_trading()
                print("\n" + format_foreign_flow(data))

            elif cmd in ["/filter", "/canslim"]:
                print("\n⏳ Đang lọc cổ phiếu theo tiêu chí Tăng trưởng & Dòng tiền...")
                candidates = engine.filter_growth_momentum(["FPT", "SSI", "HPG", "VNM", "MWG", "TCB", "DGC", "PNJ"])
                print("\n" + format_filter_results(candidates))

            elif cmd == "/market":
                print("\n⏳ Đang cập nhật chỉ số VN-INDEX...")
                overview = engine.data_loader.get_market_overview()
                print("\n" + format_market_overview(overview))

            elif cmd in ["/sub", "/watch", "/alert"]:
                if not arg:
                    print("⚠️ Vui lòng nhập mã! Ví dụ: /sub FPT")
                else:
                    alert_mgr.add_alert(chat_id=999999, symbol=arg)
                    print(f"✅ Đã đăng ký nhận cảnh báo cho mã {arg}!")

            elif cmd in ["/unsub", "/unwatch", "/unalert"]:
                if not arg:
                    print("⚠️ Vui lòng nhập mã! Ví dụ: /unsub FPT")
                else:
                    alert_mgr.remove_alert(chat_id=999999, symbol=arg)
                    print(f"🗑 Đã hủy nhận cảnh báo cho mã {arg}!")

            elif cmd in ["/watchlist", "/subs"]:
                saved = alert_mgr.get_user_alerts(chat_id=999999)
                print("\n" + format_watchlist(saved))

            elif len(cmd) == 3 and cmd.isalpha():
                print(f"\n⏳ Đang phân tích mã {cmd.upper()}...")
                analysis = engine.analyze_symbol(cmd.upper())
                print("\n" + format_analysis_card(analysis))

            else:
                print(f"⚠️ Lệnh không xác định: '{cmd_input}'. Gõ '/help' để xem danh sách lệnh.")

        except (KeyboardInterrupt, EOFError):
            print("\n👋 Đã dừng chương trình.")
            break
        except Exception as e:
            print(f"❌ Xảy ra lỗi: {e}")
# endregion

# region 3. Điểm khởi chạy 1-Click (Play in VS Code)
def get_bot_info(token: str):
    """Lấy thông tin tên và username của Bot từ Telegram API."""
    try:
        resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
        if resp.ok:
            data = resp.json().get("result", {})
            return data.get("first_name", "Fintech Bot"), data.get("username", "")
    except Exception:
        pass
    return "Fintech Bot", ""


def main():
    parser = argparse.ArgumentParser(description="Khởi chạy Telegram Bot Đầu Tư Chứng Khoán")
    parser.add_argument("--demo", action="store_true", help="Chạy chế độ mô phỏng Terminal Demo")
    parser.add_argument("--test", action="store_true", help="Chạy kiểm thử tự động toàn bộ tính năng rồi thoát")
    args = parser.parse_args()

    token = config.TELEGRAM_BOT_TOKEN

    # 1. Chế độ kiểm thử tự động
    if args.test:
        print("🧪 Đang thực hiện kiểm thử tự động toàn bộ chức năng...")
        engine = StrategyEngine()
        b_engine = BacktestEngine()
        fpt = engine.analyze_symbol("FPT")
        assert fpt["symbol"] == "FPT", "Kiểm tra FPT thất bại"
        market = engine.data_loader.get_market_overview()
        assert "close" in market, "Kiểm tra VNINDEX thất bại"
        movers = engine.data_loader.get_market_movers()
        assert "gainers" in movers, "Kiểm tra Movers thất bại"
        foreign = engine.data_loader.get_foreign_trading()
        assert "top_net_buy" in foreign, "Kiểm tra Foreign thất bại"
        df = engine.data_loader.get_history("FPT", days=90)
        c_buf = generate_stock_chart(df, "FPT", days=60)
        assert c_buf is not None, "Kiểm tra Chart thất bại"
        bt = b_engine.run(df)
        assert "win_rate" in bt, "Kiểm tra Backtest thất bại"
        print("✅ Toàn bộ kiểm thử tự động thành công (100% Pass)!")
        sys.exit(0)

    # 2. Nếu chưa có token hoặc có cờ --demo -> Mở chế độ Demo
    if args.demo or not token or token == "your_telegram_bot_token_here":
        if not token or token == "your_telegram_bot_token_here":
            print("\n" + "!" * 75)
            print("ℹ️  CHƯA PHÁT HIỆN TELEGRAM_BOT_TOKEN TRONG FILE .env")
            print("👉 Bạn có thể lấy Token miễn phí từ @BotFather trên Telegram và điền vào .env")
            print("👉 Đang tự động chuyển sang chế độ Interactive Demo CLI để bạn trải nghiệm ngay:")
            print("!" * 75)
        run_interactive_demo()
        return

    # 3. CHẾ ĐỘ 1-CLICK MẶC ĐỊNH (KHI BẤM PLAY TRÊN VS CODE): TỰ ĐỘNG CHẠY LIVE BOT
    bot_name, bot_username = get_bot_info(token)
    bot_link = f"https://t.me/{bot_username}" if bot_username else "Ứng dụng Telegram"

    print("\n" + "=" * 80)
    print("🚀 HỆ THỐNG TELEGRAM BOT ĐẦU TƯ CHỨNG KHOÁN (FINTECH BOT) - ĐANG CHẠY TRỰC TUYẾN")
    print("=" * 80)
    print(f"🤖 Tên Bot: {bot_name} (@{bot_username})")
    print(f"🔗 Link mở trực tiếp: {bot_link}")
    print(f"🟢 Trạng thái: ONLINE - Đang lắng nghe tín hiệu từ người dùng Telegram")
    print(f"🛡️  Bảo vệ hệ thống: SQLite Cache TTL 15m | Auto-fallback CafeF Anti-blocking")
    print("-" * 80)
    print("📱 CÁC LỆNH ĐẦU TƯ CHUYÊN SÂU TRÊN TELEGRAM:")
    print("   1️⃣ /signals       : Bảng tín hiệu Mua/Bán Breakout hôm nay")
    print("   2️⃣ /check <MÃ>    : Kế hoạch giao dịch (Entry, Target +14%, Stop Loss -7%)")
    print("   3️⃣ /chart <MÃ>    : Đồ thị nến Nhật trực quan (EMA 20/50, Volume MA, RSI 14)")
    print("   4️⃣ /backtest <MÃ> : Kiểm định hiệu năng thuật toán 3-6 tháng qua (Win Rate, MDD)")
    print("   5️⃣ /top           : Top cổ phiếu tăng giá & thanh khoản bùng nổ trong phiên")
    print("   6️⃣ /foreign       : Thống kê dòng tiền Khối ngoại Mua/Bán ròng")
    print("   7️⃣ /filter        : Bộ lọc siêu cổ phiếu CANSLIM (ROE > 15%, Tăng trưởng LN > 15%)")
    print("   8️⃣ /market        : Tổng quan chỉ số thị trường VN-Index")
    print("   9️⃣ /sub <MÃ>      : Đăng ký nhận cảnh báo cho mã (/unsub để hủy, /watchlist xem danh mục)")
    print("=" * 80)
    print("💡 Bot đang chạy tự động trong nền... Bấm nút đỏ hoặc nhấn Ctrl+C trên Terminal để dừng.\n")

    try:
        from src.bot.telegram_bot import TelegramStockBot
        bot = TelegramStockBot(token=token)
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Đã dừng Telegram Bot an toàn. Hẹn gặp lại!")
    except Exception as e:
        print(f"\n❌ Lỗi khởi chạy Bot: {e}")


if __name__ == "__main__":
    main()
# endregion
