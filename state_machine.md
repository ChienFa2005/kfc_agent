# KFC 優惠券推薦 AI Agent - State Machine 設計

## 狀態機架構 (Finite State Machine)

本系統使用有限狀態機 (FSM) 管理對話流程，確保 Agent 在不同階段提供適當的回應。

---

## 狀態定義 (States)

| 狀態 | 說明 | 持續時間 |
|------|------|----------|
| **IDLE** | 初始狀態，等待開始 | 一次性 |
| **ASKING_INFO** | 詢問使用者需求（人數、偏好） | 可重複 |
| **SHOW_MENU** | 顯示完整菜單 | 一次性 |
| **FILTERING** | 過濾優惠券 | 一次性 |
| **RESULTS** | 顯示推薦結果 | 持續 |
| **DONE** | 對話結束 | 終止狀態 |

---

## 事件 (Events)

| 事件 | 觸發條件 | 說明 |
|------|----------|------|
| **start** | 使用者首次啟動 | 開始對話 |
| **got_info** | 成功提取人數 + 偏好 | 資訊完整 |
| **want_menu** | 使用者說「沒想法」等 | 需要查看菜單 |
| **invalid** | 資訊不完整 | 需要補充 |
| **menu_viewed** | 使用者看完菜單 | 返回詢問 |
| **filtered** | 完成過濾 | 顯示結果 |
| **restart** | 使用者輸入「重來」 | 重置狀態 |
| **quit** | 使用者輸入「離開」 | 結束對話 |

---

## 狀態轉換圖 (State Transition Diagram)

```
┌─────────────────────────────────────────────────────────────┐
│                        KFC Agent FSM                        │
└─────────────────────────────────────────────────────────────┘

                    [使用者啟動程式]
                            │
                            ▼
                    ┌───────────────┐
                    │     IDLE      │ (初始狀態)
                    │               │
                    └───────┬───────┘
                            │ start
                            ▼
                    ┌───────────────┐
              ┌────▶│  ASKING_INFO  │◀────┐
              │     │  (詢問需求)    │     │
              │     └───────┬───────┘     │
              │             │             │
              │   ┌─────────┼─────────┐   │
              │   │         │         │   │
              │   │ invalid │ got_info│ want_menu
              │   │         │         │   │
              │   └─────────┘         │   │
              │                       ▼   │
              │               ┌──────────────┐
              │               │  FILTERING   │
              │               │  (過濾優惠)   │
              │               └──────┬───────┘
              │                      │ filtered
              │                      ▼
              │               ┌──────────────┐
              │         ┌────▶│   RESULTS    │
              │         │     │  (顯示結果)   │
              │         │     └──────┬───────┘
              │         │            │
              │         │    ┌───────┴────────┐
              │         │    │                │
              │    restart   │ continue      quit
              │         │    │                │
              │         └────┘                ▼
              │                        ┌──────────────┐
              │                        │     DONE     │
              │                        │   (結束)      │
              │                        └──────────────┘
              │
              │                        ┌──────────────┐
              └───────menu_viewed──────│  SHOW_MENU   │
                                       │  (顯示菜單)   │
                                       └──────────────┘
```

---

## 詳細狀態轉換表

### 1. IDLE → ASKING_INFO
- **觸發事件**: `start` (程式啟動)
- **動作**: 顯示歡迎訊息
- **輸出**: 引導使用者輸入人數與偏好

### 2. ASKING_INFO → FILTERING
- **觸發事件**: `got_info` (LLM 成功提取人數 + 偏好)
- **條件**: `num_people != None AND preferences != []`
- **動作**:
  - 儲存 `context.num_people`
  - 儲存 `context.preferences`
- **輸出**: 無（內部狀態）

### 3. ASKING_INFO → SHOW_MENU
- **觸發事件**: `want_menu` (使用者說「沒想法」)
- **條件**: LLM 判斷 `want_menu == true`
- **動作**: 顯示所有優惠券
- **輸出**: 格式化菜單列表

### 4. ASKING_INFO → ASKING_INFO
- **觸發事件**: `invalid` (資訊不完整)
- **條件**: `num_people == None OR preferences == []`
- **動作**: 提示使用者補充資訊
- **輸出**: 「請告訴我有幾位用餐？」或「請告訴我想吃什麼？」

### 5. SHOW_MENU → ASKING_INFO
- **觸發事件**: `menu_viewed` (任意輸入)
- **動作**: 提示使用者基於菜單提供需求
- **輸出**: 「看完了嗎？請告訴我...」

### 6. FILTERING → RESULTS
- **觸發事件**: `filtered` (自動)
- **動作**:
  - 執行過濾邏輯（關鍵詞匹配）
  - 排序結果（人數接近度、價格）
  - 儲存 `context.filtered_coupons`
- **輸出**: 格式化推薦結果

### 7. RESULTS → IDLE (restart)
- **觸發事件**: `restart` (使用者輸入「重來」)
- **動作**:
  - `agent.reset()` 清空 context
  - 重新執行 IDLE 流程
- **輸出**: 重新顯示歡迎訊息

### 8. RESULTS → DONE
- **觸發事件**: 任意輸入（非 restart）
- **動作**: 準備結束對話
- **輸出**: 「還需要其他幫助嗎？」

### 9. DONE → 結束
- **觸發事件**: `quit` (任意輸入)
- **動作**: 結束程式
- **輸出**: 「感謝使用！」

---

## LLM 整合點

### 關鍵 LLM 呼叫
本系統在 **ASKING_INFO** 狀態使用 LLM：

```python
# agent.py:161
def _extract_info(self, user_input):
    """使用 LLM 提取資訊"""
    prompt = EXTRACT_INFO_PROMPT.format(user_input=user_input)
    response = call_llm(prompt)
    # 解析 JSON 結果
    return {
        "num_people": int,
        "preferences": list,
        "want_menu": bool
    }
```

### Prompt 設計
參見 `prompts.py:EXTRACT_INFO_PROMPT`
- **輸入**: 使用者自然語言
- **輸出**: 結構化 JSON
- **功能**: 提取人數、偏好、意圖

---

## 過濾邏輯 (FILTERING 狀態)

### 演算法
1. **關鍵詞匹配**: 模糊比對 `preferences` 與 `coupon.items`
2. **人數評分**: `|coupon.serves - num_people| ≤ PEOPLE_TOLERANCE`
3. **排序**:
   - 第一排序：人數差距（越小越好）
   - 第二排序：價格（越低越好）

### 程式碼位置
`agent.py:215-254` (`_filter_and_show()`)

---

## 錯誤處理

| 錯誤情境 | 處理方式 | 狀態變化 |
|---------|---------|---------|
| LLM API 失敗 | 提示「遇到問題，請再說一次」 | 停留在當前狀態 |
| JSON 解析失敗 | 同上 | 停留在當前狀態 |
| 無符合優惠券 | 顯示「沒有找到符合的」+ 建議 | FILTERING → RESULTS |
| 使用者中斷 (Ctrl+C) | 捕捉 KeyboardInterrupt，優雅退出 | → 結束 |

---

## 可擴展性設計

### 前後端分離
- **Agent 層** (`agent.py`): 純邏輯，不依賴 I/O
- **UI 層** (`main.py`): 命令行介面
- **未來擴展**: 可輕鬆替換成 Web API (Flask/FastAPI)

### 新增狀態範例
如果要加入「收藏優惠券」功能：

```python
class State(Enum):
    # ... 現有狀態
    SAVING = "saving"  # 新增

# 在 RESULTS 狀態新增事件
if user_input == "收藏第1個":
    self.state = State.SAVING
    return self._save_coupon(1)
```

---

## 測試建議

### 測試案例

| 測試案例 | 輸入 | 預期狀態路徑 |
|---------|------|-------------|
| 正常流程 | 「3個人，想吃炸雞」 | IDLE → ASKING_INFO → FILTERING → RESULTS |
| 需要菜單 | 「2個人，沒想法」 | IDLE → ASKING_INFO → SHOW_MENU → ASKING_INFO → ... |
| 資訊不完整 | 「想吃漢堡」(缺人數) | IDLE → ASKING_INFO → ASKING_INFO (停留) |
| 重新查詢 | 在 RESULTS 輸入「重來」 | ... → RESULTS → IDLE → ASKING_INFO |
| 無結果 | 「1個人，想吃牛排」 | ... → RESULTS (顯示無符合) |

---

## 系統架構圖

```
┌──────────────┐
│    使用者     │
└──────┬───────┘
       │ 自然語言輸入
       ▼
┌──────────────────────────────────┐
│         main.py (CLI)            │
│  - 讀取輸入                       │
│  - 顯示輸出                       │
│  - 處理特殊命令 (quit/restart)    │
└──────────┬───────────────────────┘
           │ agent.process(input)
           ▼
┌──────────────────────────────────┐
│       agent.py (FSM Logic)       │
│  - 狀態轉換                       │
│  - 呼叫 LLM 提取資訊              │
│  - 執行過濾邏輯                   │
└──────────┬────────────┬──────────┘
           │            │
           │            └──────────┐
           ▼                       ▼
┌──────────────────┐    ┌─────────────────┐
│  utils.py        │    │  coupons.py     │
│  - call_llm()    │    │  - 優惠券資料    │
│  - 錯誤處理       │    │  - get_coupons()│
└──────────┬───────┘    └─────────────────┘
           │
           ▼
┌──────────────────┐
│  prompts.py      │
│  - Prompt 模板   │
└──────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│      Ollama LLM API              │
│  (老師提供的 API)                 │
└──────────────────────────────────┘
```

---

## 總結

### 符合專案要求
- ✅ **State Machine Diagram**: 完整 FSM 設計
- ✅ **LLM Integration**: 在 ASKING_INFO 使用 LLM 提取資訊
- ✅ **Structured Prompts**: `prompts.py` 管理 prompt
- ✅ **Follow-up Actions**: 根據 LLM 輸出執行狀態轉換

### 設計優勢
1. **清晰的狀態管理**: 每個狀態職責明確
2. **可測試性**: 狀態轉換邏輯易於單元測試
3. **可擴展性**: 新增狀態/事件容易
4. **錯誤恢復**: LLM 失敗不會導致狀態錯亂

---

**文件版本**: v1.0
**最後更新**: 2025-12-29
**作者**: KFC Coupon Agent Team
