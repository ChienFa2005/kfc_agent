# scraper.py
"""
KFC 優惠券爬蟲模組
直接呼叫 KFC API 取得優惠券資料，並使用 LLM 解析
"""

import json
import requests
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
from config import config
from utils import call_llm

logger = logging.getLogger(__name__)

# KFC API 設定
KFC_COUPONS_API_URL = "https://olo-api.kfcclub.com.tw/menu/v1/QueryCoupons"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0",
    "referer": "https://www.kfcclub.com.tw/",
    "origin": "https://www.kfcclub.com.tw",
}

# 資料檔案路徑
RAW_DATA_FILE = "data/raw.json"
PARSED_DATA_FILE = "data/coupons.json"


def fetch_raw() -> dict:
    """
    從 KFC API 取得原始優惠券資料

    回傳：
        API 回應的 JSON 資料
    """
    logger.info("正在從 KFC API 抓取優惠券...")

    try:
        response = requests.post(
            KFC_COUPONS_API_URL,
            headers=HEADERS,
            json={},
            timeout=20
        )
        response.raise_for_status()

        logger.info("KFC API 回應成功")
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"KFC API 請求失敗：{e}")
        raise


def to_raw_schema(payload: dict) -> List[Dict]:
    """
    將 API 回應轉換成簡化的原始格式

    參數：
        payload: KFC API 的回應資料

    回傳：
        簡化的優惠券列表
    """
    rows = payload.get("Data") or []
    coupons = []

    for item in rows:
        coupon = {
            "code": item.get("CouponCode"),
            "fcode": item.get("Fcode"),
            "price": int(item.get("Price") or 0),
            "items_raw": (item.get("Intro") or "").strip(),
            "category": item.get("Category") or "",
            "img": "https://kfcoosfs.kfcclub.com.tw/" + (item.get("ImgNameNew") or ""),
        }
        coupons.append(coupon)

    logger.info(f"已轉換 {len(coupons)} 張優惠券")
    return coupons


def parse_coupon_with_llm(raw_coupon: Dict) -> Optional[Dict]:
    """
    使用 LLM 解析優惠券資訊

    從 items_raw 提取：
    - name: 優惠券名稱
    - original_price: 原價（估算）
    - items: 包含的品項列表
    - serves: 適合人數
    - description: 詳細描述

    參數：
        raw_coupon: 原始優惠券資料

    回傳：
        解析後的優惠券資料，失敗則回傳 None
    """
    items_raw = raw_coupon.get("items_raw", "")
    price = raw_coupon.get("price", 0)

    if not items_raw:
        logger.warning(f"優惠券 {raw_coupon.get('code')} 沒有描述文字")
        return None

    # 構建 Prompt
    prompt = f"""請分析以下肯德基優惠券資訊，提取結構化資料。

優惠券描述：「{items_raw}」
優惠價格：{price}元

請提取以下資訊：
1. name：優惠券名稱（簡短，例如「炸雞桶 299元」）
2. items：包含的食物品項（陣列，例如 ["炸雞", "漢堡", "薯條"]）
3. serves：適合幾人用餐（整數，根據份量推測）
4. description：完整描述（保留原文或稍微精簡）

只回傳 JSON 格式，不要其他文字：
{{
  "name": "...",
  "items": ["...", "..."],
  "serves": 數字,
  "description": "..."
}}

範例：
輸入：「9塊香酥炸雞桶，適合全家享用」，價格 299
輸出：{{"name": "炸雞桶 299元", "items": ["炸雞"], "serves": 3, "description": "9塊香酥炸雞桶"}}

現在處理：
"""

    logger.debug(f"正在解析優惠券：{raw_coupon.get('code')}")

    # 呼叫 LLM
    response = call_llm(prompt, temperature=0.3, max_tokens=300)

    if not response:
        logger.error(f"LLM 解析失敗：{raw_coupon.get('code')}")
        return None

    # 解析 JSON
    try:
        # 清理可能的 markdown 標記
        response = response.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(response)

        # 合併資料
        result = {
            "id": raw_coupon.get("code"),
            "name": parsed.get("name"),
            "price": price,
            "items": parsed.get("items", []),
            "serves": parsed.get("serves", 1),
            "description": parsed.get("description", items_raw),
            # 保留原始資料
            "fcode": raw_coupon.get("fcode"),
            "category": raw_coupon.get("category"),
            "img": raw_coupon.get("img"),
        }

        logger.debug(f"解析成功：{result['name']}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失敗 ({raw_coupon.get('code')}): {response}")
        return None


def get_raw_coupons(save_to_file: bool = True) -> List[Dict]:
    """
    取得原始優惠券資料

    參數：
        save_to_file: 是否儲存到檔案

    回傳：
        原始優惠券列表
    """
    payload = fetch_raw()

    if not payload.get("Success", False):
        error_msg = payload.get("Message", "未知錯誤")
        logger.error(f"KFC API 錯誤：{error_msg}")
        raise RuntimeError(f"API error: {error_msg}")

    coupons = to_raw_schema(payload)

    if save_to_file:
        os.makedirs("data", exist_ok=True)
        with open(RAW_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(coupons, f, ensure_ascii=False, indent=2)
        logger.info(f"已儲存原始資料：{RAW_DATA_FILE}")

    return coupons


def parse_all_coupons(raw_coupons: List[Dict]) -> List[Dict]:
    """
    使用 LLM 解析所有優惠券

    參數：
        raw_coupons: 原始優惠券列表

    回傳：
        解析後的優惠券列表
    """
    logger.info(f"開始解析 {len(raw_coupons)} 張優惠券...")

    parsed = []
    failed = 0

    for i, raw_coupon in enumerate(raw_coupons, 1):
        logger.info(f"進度：{i}/{len(raw_coupons)}")

        result = parse_coupon_with_llm(raw_coupon)

        if result:
            parsed.append(result)
        else:
            failed += 1
            logger.warning(f"跳過優惠券：{raw_coupon.get('code')}")

    logger.info(f"解析完成：成功 {len(parsed)} 張，失敗 {failed} 張")

    return parsed


def scrape_and_parse(force_update: bool = False) -> List[Dict]:
    """
    完整的爬取與解析流程

    參數：
        force_update: 是否強制重新爬取

    回傳：
        解析後的優惠券列表
    """
    # 檢查是否有快取
    if not force_update and os.path.exists(PARSED_DATA_FILE):
        logger.info(f"從快取載入：{PARSED_DATA_FILE}")
        with open(PARSED_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"載入 {len(data['coupons'])} 張優惠券（最後更新：{data['last_updated']}）")
            return data["coupons"]

    # 爬取原始資料
    logger.info("開始爬取優惠券...")
    raw_coupons = get_raw_coupons()

    # 使用 LLM 解析
    logger.info("開始使用 LLM 解析...")
    parsed_coupons = parse_all_coupons(raw_coupons)

    # 儲存解析結果
    os.makedirs("data", exist_ok=True)
    cache_data = {
        "last_updated": datetime.now().isoformat(),
        "count": len(parsed_coupons),
        "coupons": parsed_coupons
    }

    with open(PARSED_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

    logger.info(f"已儲存解析結果：{PARSED_DATA_FILE}")

    return parsed_coupons


def load_coupons_from_cache() -> Optional[List[Dict]]:
    """
    從快取載入優惠券

    回傳：
        優惠券列表，若快取不存在則回傳 None
    """
    if not os.path.exists(PARSED_DATA_FILE):
        return None

    try:
        with open(PARSED_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["coupons"]
    except Exception as e:
        logger.error(f"載入快取失敗：{e}")
        return None


def should_update_coupons(max_age_hours: int = 24):
    """
    檢查是否需要更新優惠券資料

    參數：
        max_age_hours: 資料最大存活時間（小時），預設 24 小時

    回傳：
        (need_update: bool, reason: str)
    """
    cache_path = Path(PARSED_DATA_FILE)

    # 檢查快取檔案是否存在
    if not cache_path.exists():
        return True, "沒有快取資料"

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 檢查資料格式
        if 'coupons' not in data or not data['coupons']:
            return True, "快取資料損壞"

        # 檢查更新時間
        last_updated = data.get("last_updated")
        if not last_updated:
            return True, "無法確認資料時間"

        # 計算時間差
        last_time = datetime.fromisoformat(last_updated)
        age = datetime.now() - last_time

        if age > timedelta(hours=max_age_hours):
            hours_old = int(age.total_seconds() / 3600)
            return True, f"資料已過期（{hours_old} 小時前）"

        return False, "資料是最新的"

    except Exception as e:
        logger.error(f"檢查快取失敗：{e}")
        return True, f"檢查失敗：{e}"


if __name__ == "__main__":
    # 測試爬蟲
    import logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("KFC 優惠券爬蟲測試")
    print("=" * 60)
    print()

    # 測試 1: 抓取原始資料
    print("📥 測試 1: 抓取原始資料")
    try:
        raw = get_raw_coupons()
        print(f"✅ 成功抓取 {len(raw)} 張優惠券")
        print(f"📄 範例：{raw[0]['items_raw'][:50]}...")
    except Exception as e:
        print(f"❌ 失敗：{e}")

    print()

    # 測試 2: LLM 解析（需要 API 配置）
    print("🤖 測試 2: LLM 解析優惠券")
    print("   注意：需要先配置 LLM API")

    response = input("\n是否執行完整爬取與解析？(y/N): ")

    if response.lower() == 'y':
        try:
            coupons = scrape_and_parse(force_update=True)
            print(f"\n✅ 成功解析 {len(coupons)} 張優惠券")
            print(f"\n範例優惠券：")
            print(json.dumps(coupons[0], ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"\n❌ 失敗：{e}")
            import traceback
            traceback.print_exc()
    else:
        print("已跳過")
