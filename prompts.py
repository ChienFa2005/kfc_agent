# prompts.py
"""
LLM Prompt 模板
"""

EXTRACT_INFO_PROMPT = """從使用者訊息提取資訊。你需要靈活理解各種口語化的表達方式。

使用者說：「{user_input}」

請提取：
1. 人數（整數）
2. 食物偏好（字串陣列）
3. 是否想看菜單（布林值）

判斷規則：
- 人數：提取數字，支援多種表達方式
  * 「3個人」「三人」「3位」→ 3
  * 「我們兩個」「兩位」「2人」→ 2
  * 「一個人」「單人」「自己」→ 1
  * 「全家」「一家人」→ 推測為 4
  * 如果沒提到人數 → null

- 偏好：提取所有提到的食物類型（靈活匹配，統一用標準詞彙）
  * 「炸雞」「脆雞」「雞腿」「辣雞」→ ["炸雞"]
  * 「漢堡」「雞腿堡」「堡」→ ["漢堡"]
  * 「薯條」「薯」→ ["薯條"]
  * 「可樂」「飲料」「汽水」→ ["可樂"]
  * 「蛋塔」「蛋撻」「甜點」→ ["蛋撻"]（注意：統一用「蛋撻」，不是「蛋塔」）
  * 「雞塊」「nugget」→ ["雞塊"]
  * 如果使用者說「隨便」「都可以」→ []
  * **重要規則：**
    - 只提取使用者**明確提到**的食物
    - 絕對不要猜測或添加使用者沒說的食物
    - 如果使用者沒提到任何食物，preferences 必須是 []
    - 純數字輸入（如「45」「100」）不是食物，preferences 必須是 []

- 菜單：判斷使用者是否需要查看菜單
  * 想看菜單：「沒想法」「不知道」「隨便」「有什麼」「看菜單」「選擇困難」「推薦」→ true
  * 不想看：有明確食物偏好（只要提到任何具體食物名稱，如炸雞、漢堡、雞塊、薯條等）→ false
  * 重要：如果使用者提到任何具體食物，即使只有一個詞（如「雞塊」「炸雞」），want_menu 必須是 false
  * 重要：如果只提供人數（如「2個人」「3」），沒有明確表達想看菜單，want_menu 必須是 false

特殊情況處理：
- 如果只說「你好」「嗨」「在嗎」→ {{"num_people": null, "preferences": [], "want_menu": false}}
- 如果只提供人數「2」「3個人」→ {{"num_people": 數字, "preferences": [], "want_menu": false}}
- 如果問「多少錢」「價格」→ {{"num_people": null, "preferences": [], "want_menu": true}}
- 如果說「便宜的」「划算」→ {{"num_people": null, "preferences": [], "want_menu": true}}

回傳格式（只回傳 JSON，不要其他文字）：
{{
  "num_people": 數字或null,
  "preferences": ["食物1", "食物2"] 或 [],
  "want_menu": true或false
}}

範例：
輸入：「3個人，想吃炸雞」
輸出：{{"num_people": 3, "preferences": ["炸雞"], "want_menu": false}}

輸入：「2個人，沒想法」
輸出：{{"num_people": 2, "preferences": [], "want_menu": true}}

輸入：「我想吃脆雞和薯條」
輸出：{{"num_people": null, "preferences": ["炸雞", "薯條"], "want_menu": false}}

輸入：「一家人吃，有炸雞和蛋塔嗎」
輸出：{{"num_people": 4, "preferences": ["炸雞", "蛋撻"], "want_menu": false}}

輸入：「不知道要吃什麼，給我推薦」
輸出：{{"num_people": null, "preferences": [], "want_menu": true}}

輸入：「你好」
輸出：{{"num_people": null, "preferences": [], "want_menu": false}}

輸入：「有什麼便宜的」
輸出：{{"num_people": null, "preferences": [], "want_menu": true}}

輸入：「雞塊」
輸出：{{"num_people": null, "preferences": ["雞塊"], "want_menu": false}}

輸入：「我想吃雞塊」
輸出：{{"num_people": null, "preferences": ["雞塊"], "want_menu": false}}

輸入：「2」
輸出：{{"num_people": 2, "preferences": [], "want_menu": false}}

輸入：「3個人」
輸出：{{"num_people": 3, "preferences": [], "want_menu": false}}

輸入：「45」
輸出：{{"num_people": 45, "preferences": [], "want_menu": false}}

輸入：「100」
輸出：{{"num_people": 100, "preferences": [], "want_menu": false}}

輸入：「好了」
輸出：{{"num_people": null, "preferences": [], "want_menu": false}}

輸入：「ok」
輸出：{{"num_people": null, "preferences": [], "want_menu": false}}

現在處理：
"""