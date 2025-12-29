#!/usr/bin/env python3
# main.py
"""
KFC 優惠券推薦 AI Agent - 主程序
命令行介面入口
"""

import sys
from agent import KFCAgent
from config import config
from utils import test_connection


def print_banner():
    """印出歡迎橫幅"""
    print("\n" + "=" * 60)
    print("🍗 KFC 優惠券推薦 AI Agent")
    print("=" * 60)
    print("使用方法：")
    print("  - 正常對話即可，Agent 會引導你")
    print("  - 輸入 'quit' 或 'exit' 離開")
    print("  - 輸入 'restart' 重新開始")
    print("  - 輸入 'debug' 顯示當前狀態")
    print("=" * 60 + "\n")


def run_cli():
    """
    執行命令行介面
    """
    # 驗證配置
    is_valid, errors = config.validate()

    if not is_valid:
        print("❌ 配置錯誤：")
        for error in errors:
            print(f"   - {error}")
        print("\n請檢查 .env 檔案並重新執行。")
        return

    # 顯示配置（如果是 debug 模式）
    if config.DEBUG_MODE:
        config.print_config()
        print()

    # 測試連接
    print("🔍 正在測試 LLM 連接...\n")
    if not test_connection():
        print("\n❌ LLM 連接失敗，請檢查配置後重試。")
        response = input("\n是否繼續執行？(y/N): ")
        if response.lower() != 'y':
            return

    # 智能載入優惠券（自動檢查是否需要更新）
    from scraper import should_update_coupons, scrape_and_parse, load_coupons_from_cache

    print("📥 正在載入優惠券資料...")
    need_update, reason = should_update_coupons()

    if need_update:
        print(f"📡 {reason}，正在更新優惠券...")
        try:
            coupons = scrape_and_parse(force_update=True)
            print(f"✅ 更新完成！已載入 {len(coupons)} 張優惠券\n")
        except Exception as e:
            print(f"⚠️  更新失敗：{e}")
            cached = load_coupons_from_cache()
            if cached:
                print("   使用快取資料...\n")
                coupons = cached
                print(f"✅ 已載入 {len(coupons)} 張優惠券\n")
            else:
                print("❌ 無法載入資料，程式退出")
                return
    else:
        coupons = load_coupons_from_cache()  # 使用快取
        print(f"✅ 已載入 {len(coupons)} 張優惠券（{reason}）\n")

    # 創建 Agent
    agent = KFCAgent(coupons)

    # 顯示歡迎訊息
    print_banner()

    # 初始化對話（觸發 IDLE -> ASKING_INFO）
    response = agent.process("")
    print(f"\n{response}\n")

    # 主循環
    while True:
        try:
            # 讀取使用者輸入
            user_input = input("你 > ").strip()

            # 空輸入
            if not user_input:
                continue

            # 特殊命令
            if user_input.lower() in ['quit', 'exit', '離開', '退出']:
                print("\n👋 感謝使用！祝用餐愉快！")
                break

            if user_input.lower() in ['restart', '重來', '重新開始']:
                agent.reset()
                response = agent.process("")
                print(f"\nAgent > {response}\n")
                continue

            if user_input.lower() == 'debug':
                if config.DEBUG_MODE:
                    print(f"\n[DEBUG] 當前狀態：{agent.get_state()}")
                    print(f"[DEBUG] 上下文：{agent.context}\n")
                else:
                    print("\n💡 DEBUG 模式已關閉（在 .env 中設定 DEBUG_MODE=true 開啟）\n")
                continue

            # 處理輸入
            response = agent.process(user_input)

            # 顯示回應
            print(f"\nAgent > {response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 收到中斷信號，正在退出...")
            break

        except Exception as e:
            print(f"\n❌ 發生錯誤：{e}")
            if config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
            print()


def main():
    """主函數"""
    # 檢查命令行參數
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("KFC 優惠券推薦 AI Agent")
            print("\n使用方法：")
            print("  python main.py          # 啟動命令行介面")
            print("  python main.py --help   # 顯示幫助")
            print("  python main.py --test   # 測試 LLM 連接")
            return

        if sys.argv[1] == '--test':
            print("🔍 測試 LLM 連接...\n")
            config.print_config()
            print()
            if test_connection():
                print("\n✅ 測試通過！")
            else:
                print("\n❌ 測試失敗！")
            return

    # 執行 CLI
    run_cli()


if __name__ == "__main__":
    main()
