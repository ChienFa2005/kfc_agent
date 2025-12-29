# KFC 優惠券推薦 AI Agent - 安裝與使用指南

## 快速開始

### 1. 安裝依賴

```bash
pip3 install -r requirements.txt
```

或手動安裝核心套件：

```bash
pip3 install python-dotenv requests
```

### 2. 配置 API

編輯 `.env` 檔案，填入老師提供的 API 資訊：

```env
OLLAMA_API_URL=https://your-actual-server.com/api
OLLAMA_API_KEY=your-actual-api-key
OLLAMA_MODEL=llama2
```

**重要**: 將 `your-actual-server.com` 和 `your-actual-api-key` 替換成實際值！

### 3. 測試連接

```bash
python3 main.py --test
```

如果看到 `✅ 測試通過！` 就代表設定正確。

### 4. 啟動 Agent

```bash
python3 main.py
```

---

## 使用方式

### 基本對話

```
你 > 3個人，想吃炸雞
Agent > [顯示符合的優惠券...]
```

### 查看菜單

```
你 > 2個人，沒想法
Agent > [顯示完整菜單...]
你 > 想吃漢堡和薯條
Agent > [顯示符合的優惠券...]
```

### 重新查詢

```
你 > 重來
Agent > [重新開始...]
```

### 離開程式

```
你 > quit
```

或按 `Ctrl+C`

---

## 指令參數

```bash
python3 main.py          # 啟動 CLI
python3 main.py --help   # 顯示幫助
python3 main.py --test   # 測試 LLM 連接
```

---

## 特殊指令（在對話中）

| 指令 | 功能 |
|------|------|
| `quit`, `exit`, `離開` | 離開程式 |
| `restart`, `重來`, `重新開始` | 重新查詢 |
| `debug` | 顯示當前狀態（debug 模式） |

---

## 檔案結構

```
kfc_coupon_agent/
├── main.py              # 主程序入口 ⭐ 執行這個
├── agent.py             # FSM 狀態機邏輯
├── config.py            # 配置管理
├── utils.py             # LLM 呼叫工具
├── prompts.py           # Prompt 模板
├── coupons.py           # 優惠券資料
├── scraper.py           # 爬蟲（未來使用）
├── state_machine.md     # 狀態機設計文件
├── requirements.txt     # 依賴套件
├── .env                 # API 配置（需手動設定）
└── .gitignore           # Git 忽略檔案
```

---

## 環境變數說明

在 `.env` 檔案中可配置的變數：

| 變數名稱 | 說明 | 預設值 | 必填 |
|---------|------|--------|------|
| `OLLAMA_API_URL` | Ollama API endpoint | - | ✅ |
| `OLLAMA_API_KEY` | API 認證金鑰 | - | ✅ |
| `OLLAMA_MODEL` | 使用的模型 | `llama2` | ❌ |
| `LLM_TIMEOUT` | API 請求超時（秒） | `30` | ❌ |
| `DEBUG_MODE` | 顯示 debug 訊息 | `true` | ❌ |
| `PEOPLE_TOLERANCE` | 人數匹配容差 | `1` | ❌ |

---

## 常見問題

### Q1: 出現 `ModuleNotFoundError: No module named 'dotenv'`

**解決方式**:
```bash
pip3 install python-dotenv requests
```

### Q2: 出現 `❌ 連接失敗`

**可能原因**:
1. `.env` 檔案未正確設定
2. API URL 或 API Key 錯誤
3. 網路連接問題

**解決方式**:
```bash
# 檢查配置
python3 config.py

# 測試連接
python3 main.py --test
```

### Q3: LLM 回應太慢

**解決方式**: 調整超時設定（在 `.env`）
```env
LLM_TIMEOUT=60
```

### Q4: 想關閉 debug 訊息

**解決方式**: 在 `.env` 設定
```env
DEBUG_MODE=false
```

### Q5: 如何修改優惠券資料？

**解決方式**: 編輯 `coupons.py` 中的 `COUPONS` 列表

---

## 測試範例對話

### 範例 1: 正常流程

```
Agent > 請告訴我：
        1️⃣  有幾位用餐？
        2️⃣  大家想吃什麼？

你 > 3個人，想吃炸雞

Agent > ✅ 找到 3 張符合的優惠券：
        [顯示推薦結果...]
```

### 範例 2: 需要菜單

```
你 > 兩個人，不知道吃什麼

Agent > [顯示完整菜單]
        看完後，請告訴我有幾位用餐，想吃什麼？

你 > 我們想吃漢堡和可樂

Agent > [顯示推薦結果...]
```

### 範例 3: 資訊不完整

```
你 > 想吃炸雞

Agent > 請告訴我有幾位用餐？

你 > 3個人

Agent > [顯示推薦結果...]
```

---

## 開發相關

### 測試配置

```bash
python3 config.py
```

### 測試 LLM 連接

```bash
python3 utils.py
```

### 測試爬蟲架構

```bash
python3 scraper.py
```

### 查看狀態機設計

```bash
cat state_machine.md
```

---

## 未來擴展

### 已預留功能

1. **爬蟲自動更新** (`scraper.py`)
   - 網頁爬取
   - 圖片下載
   - OCR 文字提取
   - LLM 解析優惠券

2. **快取機制** (`coupons_cache.json`)
   - 減少重複爬取
   - 加快載入速度

3. **前後端分離**
   - Agent 邏輯獨立
   - 可輕鬆接 Web API

### 實作爬蟲步驟（未來）

1. 安裝 OCR 相關套件：
   ```bash
   pip3 install beautifulsoup4 lxml Pillow pytesseract
   ```

2. 安裝 Tesseract（macOS）：
   ```bash
   brew install tesseract tesseract-lang
   ```

3. 修改 `scraper.py` 實作 OCR 功能

4. 修改 `coupons.py` 從快取載入：
   ```python
   from scraper import get_coupons_with_scraper
   COUPONS = get_coupons_with_scraper()
   ```

---

## 專案要求檢查表

- ✅ **LLM API 整合**: `utils.py` 呼叫 Ollama API
- ✅ **State Machine Diagram**: `state_machine.md`
- ✅ **可執行代碼**: `main.py`
- ✅ **GitHub 準備**: `.gitignore` 已設定
- ✅ **超越 toy example**: 完整 FSM + 優惠券推薦系統

---

## 授權與聯絡

此專案為 TOC 2025 Final Project
如有問題請聯絡團隊成員

**最後更新**: 2025-12-29
