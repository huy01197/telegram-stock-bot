"""
Module điều khiển Telegram Bot (Telegram Bot Controller).
Xử lý toàn bộ luồng tương tác người dùng qua các lệnh (Commands) và nút bấm (Inline Keyboards):
- /signals: Bảng quét tín hiệu Mua/Bán hôm nay
- /check <MÃ>: Phân tích kỹ thuật & kế hoạch giao dịch (Entry, Target, Stop Loss)
- /chart <MÃ>: Đồ thị nến Nhật kỹ thuật trực quan (EMA20/50, Volume, RSI)
- /backtest <MÃ>: Kiểm định hiệu năng thuật toán 3-6 tháng qua (Win Rate, Return, MDD)
- /top: Top cổ phiếu tăng giá & thanh khoản bùng nổ phiên
- /foreign: Dòng tiền Khối ngoại Mua/Bán ròng
- /filter: Bộ lọc siêu cổ phiếu tăng trưởng CANSLIM
- /market: Tổng quan thị trường chứng khoán VN-Index
- /sub <MÃ>, /unsub <MÃ>: Đăng ký / Hủy nhận cảnh báo cho mã
- /watchlist: Xem danh mục cổ phiếu đang theo dõi kèm phím bấm tương tác
"""

# region 1. Thư viện & Khởi tạo Bot Controller
import io
import logging
from typing import Optional, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

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

logger = logging.getLogger(__name__)


class TelegramStockBot:
    def __init__(self, token: Optional[str] = None):
        self.token = token or config.TELEGRAM_BOT_TOKEN
        self.strategy_engine = StrategyEngine()
        self.backtest_engine = BacktestEngine()
        self.alert_manager = AlertManager()
        self.app: Optional[Application] = None
# endregion

# region 2. Bàn phím Menu Tương tác Nhanh (Inline Keyboards)
    def _get_main_keyboard(self) -> InlineKeyboardMarkup:
        """Tạo bàn phím menu tương tác nhanh tinh gọn, tập trung đầu tư."""
        keyboard = [
            [
                InlineKeyboardButton("📢 Tín hiệu hôm nay", callback_data="cmd_signals"),
                InlineKeyboardButton("🏆 Bộ lọc CANSLIM", callback_data="cmd_filter"),
            ],
            [
                InlineKeyboardButton("📊 Đồ thị FPT", callback_data="cmd_chart_FPT"),
                InlineKeyboardButton("🧪 Backtest FPT", callback_data="cmd_backtest_FPT"),
            ],
            [
                InlineKeyboardButton("🚀 Top Phiên", callback_data="cmd_top"),
                InlineKeyboardButton("🌐 Khối Ngoại", callback_data="cmd_foreign"),
            ],
            [
                InlineKeyboardButton("🏛 VN-Index", callback_data="cmd_market"),
                InlineKeyboardButton("⭐ Danh mục theo dõi", callback_data="cmd_watchlist"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def _get_stock_action_keyboard(self, symbol: str) -> InlineKeyboardMarkup:
        """Bàn phím thao tác nhanh cho một mã cổ phiếu cụ thể."""
        sym = symbol.upper()
        keyboard = [
            [
                InlineKeyboardButton(f"📊 Đồ thị {sym}", callback_data=f"cmd_chart_{sym}"),
                InlineKeyboardButton(f"🧪 Backtest {sym}", callback_data=f"cmd_backtest_{sym}"),
            ],
            [
                InlineKeyboardButton(f"🔔 Sub {sym}", callback_data=f"cmd_sub_{sym}"),
                InlineKeyboardButton(f"🔍 Chi tiết {sym}", callback_data=f"cmd_check_{sym}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
# endregion

# region 3. Các Lệnh Cơ bản (/start, /help)
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /start."""
        welcome_text = format_welcome_message()
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self._get_main_keyboard()
        )

    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /help."""
        help_text = (
            "📖 *HƯỚNG DẪN BỘ LỆNH ĐẦU TƯ FINTECH BOT*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "1️⃣ *Phân tích & Tín hiệu:*\n"
            "• `/signals`: Bảng tín hiệu Mua/Bán Breakout hôm nay\n"
            "• `/check <MÃ>`: Phân tích kỹ thuật, cơ bản và Kế hoạch vào lệnh (Target +14%, Stop -7%)\n"
            "• `/chart <MÃ>`: Xem đồ thị nến Nhật trực quan (EMA 20/50, Volume, RSI)\n"
            "• `/backtest <MÃ>`: Kiểm định thuật toán 3-6 tháng qua (Win Rate %, MDD %)\n\n"
            "2️⃣ *Dòng tiền & Thị trường:*\n"
            "• `/top`: Top cổ phiếu tăng giá & thanh khoản bùng nổ trong ngày\n"
            "• `/foreign`: Thống kê dòng tiền Khối ngoại Mua/Bán ròng\n"
            "• `/filter`: Bộ lọc siêu cổ phiếu CANSLIM (ROE > 15%, Tăng trưởng LN > 15%)\n"
            "• `/market`: Báo cáo chỉ số thị trường VN-Index\n\n"
            "3️⃣ *Quản lý Đăng ký Nhận Cảnh báo:*\n"
            "• `/sub <MÃ>`: Đăng ký nhận cảnh báo tự động cho mã (vd: `/sub FPT`)\n"
            "• `/unsub <MÃ>`: Hủy nhận cảnh báo cho mã (vd: `/unsub FPT`)\n"
            "• `/watchlist`: Xem danh mục các mã bạn đã đăng ký\n\n"
            "💡 _Mẹo: Bạn có thể gõ trực tiếp 3 chữ cái mã cổ phiếu (ví dụ: `FPT`, `SSI`, `HPG`) để xem nhanh phân tích!_"
        )
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self._get_main_keyboard()
        )
# endregion

# region 4. Các Lệnh Phân Tích Kỹ Thuật & Đồ Thị (/signals, /check, /chart, /backtest)
    async def signals_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /signals."""
        msg_waiting = await update.message.reply_text("⏳ *Đang quét tín hiệu thị trường hôm nay...*", parse_mode=ParseMode.MARKDOWN)
        scan_res = self.strategy_engine.scan_watchlist()
        reply_text = format_signals_summary(scan_res)
        await msg_waiting.edit_text(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=self._get_main_keyboard())

    async def check_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /check <MÃ>."""
        args = context.args
        symbol = args[0].upper().strip() if args else "FPT"
        msg_waiting = await update.message.reply_text(f"⏳ *Đang phân tích dữ liệu cho mã {symbol}...*", parse_mode=ParseMode.MARKDOWN)
        analysis = self.strategy_engine.analyze_symbol(symbol)
        card_text = format_analysis_card(analysis)
        await msg_waiting.edit_text(
            card_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self._get_stock_action_keyboard(symbol)
        )

    async def chart_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /chart <MÃ> (Sinh ảnh đồ thị nến Nhật)."""
        args = context.args
        symbol = args[0].upper().strip() if args else "FPT"
        msg_waiting = await update.message.reply_text(f"⏳ *Đang vẽ đồ thị nến kỹ thuật cho {symbol}...*", parse_mode=ParseMode.MARKDOWN)

        df = self.strategy_engine.data_loader.get_history(symbol=symbol, days=90)
        chart_buf = generate_stock_chart(df, symbol=symbol, days=60)

        if chart_buf is not None:
            await update.message.reply_photo(
                photo=chart_buf,
                caption=f"📊 *Đồ thị kỹ thuật {symbol}* (Nến Nhật, EMA 20/50, Volume MA20, RSI 14)\n_Gõ `/check {symbol}` để xem kế hoạch giao dịch._",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self._get_stock_action_keyboard(symbol)
            )
            await msg_waiting.delete()
        else:
            await msg_waiting.edit_text(
                f"❌ Không thể tạo đồ thị cho mã *{symbol}*. Vui lòng kiểm tra lại mã cổ phiếu!",
                parse_mode=ParseMode.MARKDOWN
            )

    async def backtest_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /backtest <MÃ> [tháng]."""
        args = context.args
        symbol = args[0].upper().strip() if args else "FPT"
        months = 6
        if len(args) > 1:
            try:
                months = max(1, min(12, int(args[1])))
            except ValueError:
                pass

        days = months * 35
        msg_waiting = await update.message.reply_text(f"⏳ *Đang chạy kiểm định chiến lược cho {symbol} trong {months} tháng qua...*", parse_mode=ParseMode.MARKDOWN)

        df = self.strategy_engine.data_loader.get_history(symbol=symbol, days=days)
        res = self.backtest_engine.run(df)
        report_text = format_backtest_report(symbol, res, months=months)

        await msg_waiting.edit_text(
            report_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self._get_stock_action_keyboard(symbol)
        )
# endregion

# region 5. Các Lệnh Thị Trường & Dòng Tiền (/top, /foreign, /filter, /market)
    async def top_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /top (Top biến động & Khối lượng phiên)."""
        msg_waiting = await update.message.reply_text("⏳ *Đang cập nhật bảng xếp hạng phiên hôm nay...*", parse_mode=ParseMode.MARKDOWN)
        data = self.strategy_engine.data_loader.get_market_movers()
        reply_text = format_top_movers(data)
        await msg_waiting.edit_text(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=self._get_main_keyboard())

    async def foreign_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /foreign (Dòng tiền Khối ngoại)."""
        msg_waiting = await update.message.reply_text("⏳ *Đang thống kê giao dịch Khối ngoại hôm nay...*", parse_mode=ParseMode.MARKDOWN)
        data = self.strategy_engine.data_loader.get_foreign_trading()
        reply_text = format_foreign_flow(data)
        await msg_waiting.edit_text(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=self._get_main_keyboard())

    async def filter_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /filter (Bộ lọc CANSLIM)."""
        msg_waiting = await update.message.reply_text("⏳ *Đang lọc các siêu cổ phiếu Tăng trưởng & Dòng tiền bùng nổ...*", parse_mode=ParseMode.MARKDOWN)
        candidates = self.strategy_engine.filter_growth_momentum()
        reply_text = format_filter_results(candidates)
        await msg_waiting.edit_text(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=self._get_main_keyboard())

    async def market_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /market."""
        market_info = self.strategy_engine.data_loader.get_market_overview()
        reply_text = format_market_overview(market_info)
        await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=self._get_main_keyboard())
# endregion

# region 6. Đăng ký & Quản lý Danh mục Nhận Cảnh báo (/sub, /unsub, /watchlist)
    async def sub_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /sub <MÃ> (Đăng ký nhận cảnh báo)."""
        args = context.args
        chat_id = update.effective_chat.id
        if not args:
            await update.message.reply_text("⚠️ Vui lòng cung cấp mã muốn đăng ký! Ví dụ: `/sub FPT` hoặc `/sub SSI`", parse_mode=ParseMode.MARKDOWN)
            return

        symbol = args[0].upper().strip()
        ok = self.alert_manager.add_alert(chat_id, symbol)
        if ok:
            await update.message.reply_text(
                f"✅ *Đã đăng ký nhận cảnh báo thành công cho mã {symbol}!*\n"
                f"Hệ thống sẽ tự động giám sát và gửi thông báo khi có tín hiệu nổ vol hoặc điểm mua mới.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self._get_stock_action_keyboard(symbol)
            )
        else:
            await update.message.reply_text(f"❌ Không thể đăng ký mã *{symbol}*.", parse_mode=ParseMode.MARKDOWN)

    async def unsub_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /unsub <MÃ> (Hủy nhận cảnh báo)."""
        args = context.args
        chat_id = update.effective_chat.id
        if not args:
            await update.message.reply_text("⚠️ Vui lòng cung cấp mã muốn hủy đăng ký: `/unsub <MÃ>`", parse_mode=ParseMode.MARKDOWN)
            return

        symbol = args[0].upper().strip()
        self.alert_manager.remove_alert(chat_id, symbol)
        await update.message.reply_text(f"🗑 Đã hủy nhận cảnh báo cho mã *{symbol}*.", parse_mode=ParseMode.MARKDOWN)

    # Aliases cho tương thích ngược
    watch_handler = sub_handler
    unwatch_handler = unsub_handler

    async def watchlist_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /watchlist hoặc /subs."""
        chat_id = update.effective_chat.id
        saved = self.alert_manager.get_user_alerts(chat_id)
        msg_text = format_watchlist(saved)

        # Tạo keyboard thao tác nhanh cho từng mã đã lưu
        keyboard = []
        for s in saved[:6]:
            keyboard.append([
                InlineKeyboardButton(f"📊 Đồ thị {s}", callback_data=f"cmd_chart_{s}"),
                InlineKeyboardButton(f"🔍 Soi {s}", callback_data=f"cmd_check_{s}"),
                InlineKeyboardButton(f"❌ Hủy sub", callback_data=f"cmd_unsub_{s}"),
            ])
        keyboard.append([InlineKeyboardButton("🔙 Menu Chính", callback_data="cmd_menu")])

        reply_markup = InlineKeyboardMarkup(keyboard) if saved else self._get_main_keyboard()
        await update.message.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    async def text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý tin nhắn văn bản thông thường (người dùng gõ thẳng 3 chữ cái mã cổ phiếu)."""
        text = update.message.text.strip().upper()
        if len(text) == 3 and text.isalpha():
            msg_waiting = await update.message.reply_text(f"⏳ *Đang phân tích {text}...*", parse_mode=ParseMode.MARKDOWN)
            analysis = self.strategy_engine.analyze_symbol(text)
            card_text = format_analysis_card(analysis)
            await msg_waiting.edit_text(
                card_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self._get_stock_action_keyboard(text)
            )
        else:
            await update.message.reply_text(
                "💡 Gõ `/help` để xem danh sách lệnh hoặc gõ trực tiếp 3 chữ cái mã cổ phiếu (ví dụ: `FPT`, `HPG`, `SSI`).",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self._get_main_keyboard()
            )
# endregion

# region 7. Xử lý Sự kiện Nút bấm Tương tác (Callback Query)
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý sự kiện bấm nút trên Inline Keyboard."""
        query = update.callback_query
        await query.answer()
        data = query.data
        chat_id = update.effective_chat.id

        if data == "cmd_signals":
            await query.edit_message_text("⏳ *Đang quét tín hiệu hôm nay...*", parse_mode=ParseMode.MARKDOWN)
            scan_res = self.strategy_engine.scan_watchlist()
            reply_text = format_signals_summary(scan_res)
            await query.edit_message_text(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=self._get_main_keyboard())

        elif data.startswith("cmd_check_"):
            symbol = data.replace("cmd_check_", "")
            await query.edit_message_text(f"⏳ *Đang phân tích mã {symbol}...*", parse_mode=ParseMode.MARKDOWN)
            analysis = self.strategy_engine.analyze_symbol(symbol)
            card_text = format_analysis_card(analysis)
            await query.edit_message_text(
                card_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self._get_stock_action_keyboard(symbol)
            )

        elif data.startswith("cmd_chart_"):
            symbol = data.replace("cmd_chart_", "")
            await query.edit_message_text(f"⏳ *Đang vẽ đồ thị nến cho {symbol}...*", parse_mode=ParseMode.MARKDOWN)
            df = self.strategy_engine.data_loader.get_history(symbol=symbol, days=90)
            chart_buf = generate_stock_chart(df, symbol=symbol, days=60)
            if chart_buf:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=chart_buf,
                    caption=f"📊 *Đồ thị kỹ thuật {symbol}*\n_Gõ `/check {symbol}` để xem kế hoạch giao dịch._",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self._get_stock_action_keyboard(symbol)
                )
                await query.delete_message()
            else:
                await query.edit_message_text(f"❌ Không thể tạo đồ thị cho {symbol}.", reply_markup=self._get_main_keyboard())

        elif data.startswith("cmd_backtest_"):
            symbol = data.replace("cmd_backtest_", "")
            await query.edit_message_text(f"⏳ *Đang kiểm định chiến lược cho {symbol}...*", parse_mode=ParseMode.MARKDOWN)
            df = self.strategy_engine.data_loader.get_history(symbol=symbol, days=210)
            res = self.backtest_engine.run(df)
            report_text = format_backtest_report(symbol, res, months=6)
            await query.edit_message_text(
                report_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self._get_stock_action_keyboard(symbol)
            )

        elif data.startswith("cmd_sub_") or data.startswith("cmd_watch_"):
            prefix = "cmd_sub_" if data.startswith("cmd_sub_") else "cmd_watch_"
            symbol = data.replace(prefix, "")
            self.alert_manager.add_alert(chat_id, symbol)
            await query.answer(f"Đã đăng ký nhận cảnh báo cho {symbol}!", show_alert=True)

        elif data.startswith("cmd_unsub_") or data.startswith("cmd_unwatch_"):
            prefix = "cmd_unsub_" if data.startswith("cmd_unsub_") else "cmd_unwatch_"
            symbol = data.replace(prefix, "")
            self.alert_manager.remove_alert(chat_id, symbol)
            saved = self.alert_manager.get_user_alerts(chat_id)
            msg_text = format_watchlist(saved)
            keyboard = []
            for s in saved[:6]:
                keyboard.append([
                    InlineKeyboardButton(f"📊 Đồ thị {s}", callback_data=f"cmd_chart_{s}"),
                    InlineKeyboardButton(f"🔍 Soi {s}", callback_data=f"cmd_check_{s}"),
                    InlineKeyboardButton(f"❌ Hủy sub", callback_data=f"cmd_unsub_{s}"),
                ])
            keyboard.append([InlineKeyboardButton("🔙 Menu Chính", callback_data="cmd_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard) if saved else self._get_main_keyboard()
            await query.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        elif data == "cmd_top":
            await query.edit_message_text("⏳ *Đang cập nhật bảng xếp hạng phiên hôm nay...*", parse_mode=ParseMode.MARKDOWN)
            m_data = self.strategy_engine.data_loader.get_market_movers()
            await query.edit_message_text(format_top_movers(m_data), parse_mode=ParseMode.MARKDOWN, reply_markup=self._get_main_keyboard())

        elif data == "cmd_foreign":
            await query.edit_message_text("⏳ *Đang thống kê dòng tiền Khối ngoại...*", parse_mode=ParseMode.MARKDOWN)
            f_data = self.strategy_engine.data_loader.get_foreign_trading()
            await query.edit_message_text(format_foreign_flow(f_data), parse_mode=ParseMode.MARKDOWN, reply_markup=self._get_main_keyboard())

        elif data == "cmd_filter":
            await query.edit_message_text("⏳ *Đang áp dụng bộ lọc Tăng trưởng & Dòng tiền...*", parse_mode=ParseMode.MARKDOWN)
            candidates = self.strategy_engine.filter_growth_momentum()
            reply_text = format_filter_results(candidates)
            await query.edit_message_text(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=self._get_main_keyboard())

        elif data == "cmd_market":
            market_info = self.strategy_engine.data_loader.get_market_overview()
            reply_text = format_market_overview(market_info)
            await query.edit_message_text(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=self._get_main_keyboard())

        elif data in ["cmd_watchlist", "cmd_my_alerts"]:
            saved = self.alert_manager.get_user_alerts(chat_id)
            msg_text = format_watchlist(saved)
            keyboard = []
            for s in saved[:6]:
                keyboard.append([
                    InlineKeyboardButton(f"📊 Đồ thị {s}", callback_data=f"cmd_chart_{s}"),
                    InlineKeyboardButton(f"🔍 Soi {s}", callback_data=f"cmd_check_{s}"),
                    InlineKeyboardButton(f"❌ Hủy sub", callback_data=f"cmd_unsub_{s}"),
                ])
            keyboard.append([InlineKeyboardButton("🔙 Menu Chính", callback_data="cmd_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard) if saved else self._get_main_keyboard()
            await query.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        elif data == "cmd_menu":
            await query.edit_message_text(format_welcome_message(), parse_mode=ParseMode.MARKDOWN, reply_markup=self._get_main_keyboard())
# endregion

# region 8. Đăng ký Tuyến đường & Thiết lập Menu Lệnh Telegram
    async def _post_init(self, application: Application):
        """Tự động đăng ký danh sách lệnh trực tiếp lên giao diện Telegram."""
        commands = [
            BotCommand("signals", "Bảng tín hiệu Mua/Bán hôm nay"),
            BotCommand("check", "Phân tích & Kế hoạch vào lệnh cổ phiếu"),
            BotCommand("chart", "Đồ thị nến Nhật trực quan (EMA, Volume, RSI)"),
            BotCommand("backtest", "Kiểm định hiệu năng chiến lược lịch sử"),
            BotCommand("top", "Top cổ phiếu biến động & khối lượng lớn"),
            BotCommand("foreign", "Thống kê dòng tiền Khối ngoại Mua/Bán"),
            BotCommand("filter", "Bộ lọc siêu cổ phiếu CANSLIM"),
            BotCommand("market", "Tổng quan chỉ số thị trường VN-Index"),
            BotCommand("sub", "Đăng ký nhận cảnh báo cho mã"),
            BotCommand("unsub", "Hủy nhận cảnh báo cho mã"),
            BotCommand("watchlist", "Xem danh mục cổ phiếu đã đăng ký"),
            BotCommand("help", "Xem hướng dẫn chi tiết"),
        ]
        try:
            await application.bot.set_my_commands(commands)
        except Exception as e:
            logger.warning(f"Không thể thiết lập set_my_commands: {e}")

    def build_application(self) -> Application:
        """Khởi tạo và đăng ký các route handler cho bot."""
        if not self.token or self.token == "your_telegram_bot_token_here":
            raise ValueError("Chưa thiết lập TELEGRAM_BOT_TOKEN hợp lệ trong file .env hoặc biến môi trường!")

        self.app = ApplicationBuilder().token(self.token).post_init(self._post_init).build()

        # Đăng ký Command Handlers
        self.app.add_handler(CommandHandler("start", self.start_handler))
        self.app.add_handler(CommandHandler("help", self.help_handler))
        self.app.add_handler(CommandHandler("signals", self.signals_handler))
        self.app.add_handler(CommandHandler("check", self.check_handler))
        self.app.add_handler(CommandHandler("chart", self.chart_handler))
        self.app.add_handler(CommandHandler("backtest", self.backtest_handler))
        self.app.add_handler(CommandHandler("top", self.top_handler))
        self.app.add_handler(CommandHandler("foreign", self.foreign_handler))
        self.app.add_handler(CommandHandler("filter", self.filter_handler))
        self.app.add_handler(CommandHandler("market", self.market_handler))
        self.app.add_handler(CommandHandler("sub", self.sub_handler))
        self.app.add_handler(CommandHandler("unsub", self.unsub_handler))
        self.app.add_handler(CommandHandler("watchlist", self.watchlist_handler))

        # Aliases tương thích ngược
        self.app.add_handler(CommandHandler("watch", self.sub_handler))
        self.app.add_handler(CommandHandler("unwatch", self.unsub_handler))
        self.app.add_handler(CommandHandler("alert", self.sub_handler))
        self.app.add_handler(CommandHandler("unalert", self.unsub_handler))
        self.app.add_handler(CommandHandler("subs", self.watchlist_handler))
        self.app.add_handler(CommandHandler("today", self.signals_handler))
        self.app.add_handler(CommandHandler("canslim", self.filter_handler))

        # Handlers phím bấm và tin nhắn thường
        self.app.add_handler(CallbackQueryHandler(self.callback_handler))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_handler))

        return self.app

    def run(self):
        """Khởi chạy Bot ở chế độ Polling."""
        app = self.build_application()
        print("🤖 Telegram Bot đang chạy ở chế độ Polling... Nhấn Ctrl+C để dừng.")
        app.run_polling()
# endregion
