"""
Script thực thi Backtesting độc lập.
Đánh giá hiệu năng của 2 chiến lược trên dữ liệu thực tế 3 - 6 tháng gần nhất.
Xuất kết quả trực quan ra màn hình và hỗ trợ xuất báo cáo.
"""

# region 1. Thư viện & Khởi tạo
import argparse
from typing import List
from src.data.data_loader import DataLoader
from src.backtest.engine import BacktestEngine
import config
# endregion

# region 2. Hàm Thực thi Backtest & Định dạng Bảng
def run_backtest(symbols: List[str], days: int = 180, strategy: str = "TA"):
    loader = DataLoader()
    engine = BacktestEngine(
        stop_loss_pct=config.RISK_CONFIG["stop_loss_pct"],
        take_profit_pct=config.RISK_CONFIG["take_profit_pct"]
    )

    print(f"\n" + "=" * 80)
    print(f"📊 KẾT QUẢ KIỂM ĐỊNH HIỆU NĂNG (BACKTESTING) - {days} NGÀY GẦN NHẤT")
    print(f"Chiến lược: {strategy} | Stop Loss: {config.RISK_CONFIG['stop_loss_pct']*100}% | Take Profit: {config.RISK_CONFIG['take_profit_pct']*100}%")
    print("=" * 80)

    results_table = []
    total_trades_all = 0
    total_wins_all = 0
    returns_all = []

    for sym in symbols:
        df = loader.get_history(sym, days=days)
        if df.empty or len(df) < 50:
            print(f"⚠️  {sym}: Không đủ dữ liệu lịch sử.")
            continue

        res = engine.run(df, strategy_type=strategy)
        total_trades_all += res["total_trades"]
        total_wins_all += res["win_trades"]
        returns_all.append(res["total_return"])

        results_table.append({
            "Mã": sym,
            "Số lệnh": res["total_trades"],
            "Thắng": res["win_trades"],
            "Thua": res["loss_trades"],
            "Win Rate (%)": f"{res['win_rate']:.1f}%",
            "Lợi nhuận (%)": f"{res['total_return']:+.2f}%",
            "Profit Factor": f"{res['profit_factor']:.2f}",
            "Max Drawdown": f"{res['max_drawdown']:.2f}%"
        })

    # In kết quả dạng bảng
    header = f"{'Mã':<6} | {'Số lệnh':<8} | {'Thắng':<6} | {'Thua':<6} | {'Win Rate':<10} | {'Lợi nhuận':<12} | {'Profit Factor':<14} | {'Max DD':<10}"
    print(header)
    print("-" * len(header))
    for r in results_table:
        print(f"{r['Mã']:<6} | {r['Số lệnh']:<8} | {r['Thắng']:<6} | {r['Thua']:<6} | {r['Win Rate (%)']:<10} | {r['Lợi nhuận (%)']:<12} | {r['Profit Factor']:<14} | {r['Max Drawdown']:<10}")
    print("-" * len(header))

    avg_win_rate = (total_wins_all / total_trades_all * 100) if total_trades_all > 0 else 0.0
    avg_return = sum(returns_all) / len(returns_all) if returns_all else 0.0
    print(f"TỔNG KẾT: Tổng số lệnh = {total_trades_all} | Tỷ lệ thắng trung bình = {avg_win_rate:.1f}% | Lợi nhuận TB = {avg_return:+.2f}%\n")
# endregion

# region 3. Giao diện Dòng lệnh (CLI Parser)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy Backtesting cho Telegram Bot chứng khoán")
    parser.add_argument("--symbols", type=str, default="FPT,SSI,HPG,VNM,MWG,TCB", help="Danh sách mã cách nhau bởi dấu phẩy")
    parser.add_argument("--days", type=int, default=180, help="Số ngày lịch sử (ví dụ 180 = ~6 tháng)")
    parser.add_argument("--strategy", type=str, default="TA", choices=["TA", "GROWTH"], help="Chiến lược (TA hoặc GROWTH)")

    args = parser.parse_args()
    sym_list = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    run_backtest(sym_list, days=args.days, strategy=args.strategy)
# endregion
