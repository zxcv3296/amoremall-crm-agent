# -*- coding: utf-8 -*-
"""
아모레몰 크롤러 v3 (DOM 기반)
==============================
- 아모레퍼시픽 32개 브랜드 크롤링
- DOM에서 상품 링크 추출 후 상세 페이지에서 정보 수집
- 10개 카테고리 매핑
- ProdCode 포함

Phase 1: 제품 크롤링
Phase 2: 리뷰 크롤링 (별도)
"""

import json
import re
import time
import os
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

# 저장 경로
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SAVE_DIR, "crawled_products.json")
LOG_FILE = os.path.join(SAVE_DIR, "crawl_log.txt")

# URL 패턴
BRAND_LIST_URL = "https://www.amoremall.com/kr/ko/display/brand"
BRAND_ALL_URL = "https://www.amoremall.com/kr/ko/display/brand/detail/all?brandSn={brand_sn}&sort=Bestselling"

# 카테고리 매핑 (ID -> 이름)
MAIN_CATEGORIES = {
    97: "스킨케어", 98: "메이크업", 99: "향수", 100: "생활용품",
    101: "소품&도구", 102: "뷰티푸드", 103: "남성", 104: "베이비",
    375: "뷰티디바이스", 384: "반려동물용품"
}

SUB_CATEGORIES = {
    126: "클렌징", 127: "모이스처라이징", 128: "스페셜케어", 129: "선케어", 130: "세트", 381: "리필",
    131: "페이스", 132: "립", 133: "아이", 134: "치크", 135: "키트&팔레트", 361: "네일", 382: "리필",
    136: "헤어케어", 137: "바디케어", 138: "구강케어", 139: "세트", 383: "리필"
}


def log(msg: str):
    """로그 출력 및 파일 저장"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    except:
        pass


def setup_driver():
    """Selenium WebDriver 설정"""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)

    return driver


def get_brands(driver) -> List[Dict]:
    """브랜드 목록 조회 (하드코딩된 목록 사용 - 24개 주요 브랜드)"""
    from amore_brands import AMORE_BRANDS
    log(f"아모레퍼시픽 브랜드 {len(AMORE_BRANDS)}개 로드")
    return AMORE_BRANDS


def get_product_links(driver, brand_sn: int, brand_name: str, max_scrolls: int = 50) -> List[Dict]:
    """브랜드 페이지에서 상품 링크 추출"""
    log(f"  [{brand_name}] 상품 링크 수집 중...")

    url = BRAND_ALL_URL.format(brand_sn=brand_sn)
    driver.get(url)
    time.sleep(3)

    # 무한 스크롤로 모든 상품 로드
    last_count = 0
    same_count = 0

    for i in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

        links = driver.find_elements("css selector", "a[href*='/product/detail']")
        current_count = len(links)

        if current_count == last_count:
            same_count += 1
            if same_count >= 3:
                break
        else:
            same_count = 0
            last_count = current_count

        if (i + 1) % 10 == 0:
            log(f"    스크롤 {i+1}: {current_count}개")

    # 링크에서 상품 정보 추출
    products = []
    seen = set()

    links = driver.find_elements("css selector", "a[href*='/product/detail']")

    for link in links:
        try:
            href = link.get_attribute("href")
            if not href:
                continue

            # URL 파싱
            prod_sn_match = re.search(r'onlineProdSn=(\d+)', href)
            prod_code_match = re.search(r'onlineProdCode=(\d+)', href)

            if prod_sn_match:
                prod_sn = int(prod_sn_match.group(1))

                if prod_sn in seen:
                    continue
                seen.add(prod_sn)

                prod = {
                    "onlineProdSn": prod_sn,
                    "onlineProdCode": prod_code_match.group(1) if prod_code_match else "",
                    "brandSn": brand_sn,
                    "brandName": brand_name,
                    "url": href
                }

                # 상품명/가격 추출 시도 (부모 요소에서)
                try:
                    parent = link.find_element("xpath", "./..")
                    text = parent.text

                    # 상품명 (첫 줄)
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    if lines:
                        # 가격이 아닌 첫 줄이 상품명
                        for line in lines:
                            if not re.match(r'^[\d,]+원?$', line) and not re.match(r'^\d+%$', line):
                                prod["prodName"] = line
                                break

                    # 가격 (숫자,원 패턴)
                    price_match = re.search(r'([\d,]+)원', text)
                    if price_match:
                        prod["salePrice"] = int(price_match.group(1).replace(',', ''))

                except:
                    pass

                products.append(prod)

        except Exception:
            continue

    log(f"  [{brand_name}] {len(products)}개 상품 링크 수집")
    return products


def get_product_detail(driver, prod: Dict) -> Dict:
    """상품 상세 페이지에서 정보 추출 (v2 - 정확한 JSON 구조)"""
    try:
        url = prod.get("url")
        if not url:
            return prod

        driver.get(url)
        time.sleep(2)

        html = driver.page_source
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)

        if match:
            data = json.loads(match.group(1))

            # initialState 파싱 (문자열일 수 있음)
            page_props = data.get("props", {}).get("pageProps", {})
            initial_state = page_props.get("initialState", {})

            if isinstance(initial_state, str):
                initial_state = json.loads(initial_state)

            # productDetail.productInfo 에서 정보 추출
            prod_detail = initial_state.get("productDetail", {})
            prod_info = prod_detail.get("productInfo", {})

            if prod_info:
                # 기본 정보
                prod["onlineProdSn"] = prod_info.get("onlineProdSn") or prod.get("onlineProdSn")
                prod["onlineProdCode"] = prod_info.get("onlineProdCode") or prod.get("onlineProdCode", "")
                prod["prodName"] = prod_info.get("onlineProdName") or prod.get("prodName", "")
                prod["description"] = prod_info.get("linePromoDesc", "")

                # 브랜드 정보
                brand_info = prod_info.get("brandInfo", {})
                if brand_info:
                    prod["brandName"] = brand_info.get("brandName") or prod.get("brandName", "")

                # 카테고리 정보 (categoryGroupInfo: large/middle/small)
                cat_info = prod_info.get("categoryInfo", {})
                cat_group = cat_info.get("categoryGroupInfo", {})
                if cat_group:
                    prod["mainCategory"] = cat_group.get("large", "")
                    prod["subCategory"] = cat_group.get("middle", "")
                    prod["detailCategory"] = cat_group.get("small", "")

                # 리뷰 정보 (reviewInfo)
                review_info = prod_info.get("reviewInfo", {})
                if review_info:
                    prod["reviewCount"] = review_info.get("reviewCount", 0)
                    prod["avgRating"] = round(review_info.get("reviewScope", 0), 2)

                # 이미지 정보
                online_images = prod_info.get("onlineImages", [])
                if online_images:
                    prod["imageUrl"] = online_images[0].get("imgUrl", "")

                # 가격 정보 (onlinePriceInfo.priceInfo 또는 products[0].prodPriceInfo.priceInfo)
                online_price = prod_info.get("onlinePriceInfo", {})
                price_data = online_price.get("priceInfo", {})

                if price_data:
                    prod["price"] = price_data.get("beforeSalePrice", 0)
                    prod["salePrice"] = price_data.get("discountedPrice", 0) or price_data.get("beforeSalePrice", 0)
                    prod["discountRate"] = price_data.get("discountRate", 0)
                else:
                    # fallback: products[0].prodPriceInfo.priceInfo
                    products_list = prod_info.get("products", [])
                    if products_list:
                        first_product = products_list[0]
                        prod_price = first_product.get("prodPriceInfo", {}).get("priceInfo", {})
                        if prod_price:
                            prod["price"] = prod_price.get("beforeSalePrice", 0)
                            prod["salePrice"] = prod_price.get("discountedPrice", 0) or prod_price.get("beforeSalePrice", 0)
                            prod["discountRate"] = prod_price.get("discountRate", 0)

                # 성분 정보
                ingredients = prod_info.get("ingredients", [])
                if ingredients:
                    prod["ingredients"] = ingredients[0].get("content", "") if isinstance(ingredients[0], dict) else ""

    except Exception as e:
        # 오류 시 기존 정보 유지
        pass

    return prod


def crawl_brand(driver, brand: Dict, get_details: bool = True) -> List[Dict]:
    """단일 브랜드 크롤링"""
    # 1. 상품 링크 수집
    products = get_product_links(driver, brand["brandSn"], brand["brandName"])

    # 2. 상세 정보 수집 (선택)
    if get_details and products:
        log(f"  [{brand['brandName']}] 상세 정보 수집 중...")
        for i, prod in enumerate(products):
            prod = get_product_detail(driver, prod)
            products[i] = prod

            if (i + 1) % 20 == 0:
                log(f"    {i+1}/{len(products)} 완료")

            time.sleep(0.5)  # 서버 부하 방지

    return products


def crawl_all(test_mode: bool = False, get_details: bool = True):
    """전체 크롤링"""
    log("=" * 60)
    log("아모레몰 크롤링 시작" + (" (테스트)" if test_mode else ""))
    log("=" * 60)

    driver = None
    all_products = []
    brands = []

    try:
        driver = setup_driver()
        log("WebDriver 초기화 완료")

        # 1. 브랜드 목록
        brands = get_brands(driver)

        if test_mode:
            brands = brands[:2]  # 테스트: 2개 브랜드만
            log(f"테스트 모드: {len(brands)}개 브랜드만")

        # 2. 브랜드별 크롤링
        for i, brand in enumerate(brands, 1):
            log(f"\n[{i}/{len(brands)}] {brand['brandName']}")

            try:
                products = crawl_brand(driver, brand, get_details=get_details)
                all_products.extend(products)
            except Exception as e:
                log(f"  ERROR: {e}")
                continue

            time.sleep(2)

        log(f"\n총 {len(all_products)}개 상품 수집")

    except Exception as e:
        log(f"크롤링 오류: {e}")
        import traceback
        log(traceback.format_exc())

    finally:
        if driver:
            driver.quit()
            log("WebDriver 종료")

    # 3. 저장
    if all_products:
        save_data = {
            "crawled_at": datetime.now().isoformat(),
            "brand_count": len(brands),
            "product_count": len(all_products),
            "brands": brands,
            "products": all_products
        }

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        log(f"저장 완료: {DATA_FILE}")

    log("=" * 60)
    log("크롤링 완료!")
    log("=" * 60)

    return all_products


def quick_test():
    """빠른 테스트 (설화수 5개 상품)"""
    log("=" * 60)
    log("빠른 테스트")
    log("=" * 60)

    driver = None

    try:
        driver = setup_driver()

        # 설화수 상품 링크 수집 (스크롤 3번만)
        products = get_product_links(driver, 18, "설화수", max_scrolls=3)

        # 처음 5개만 상세 정보
        log(f"\n상세 정보 수집 (5개)...")
        for i, prod in enumerate(products[:5]):
            prod = get_product_detail(driver, prod)
            products[i] = prod
            time.sleep(0.5)

        # 결과 출력
        log(f"\n수집 결과: {len(products)}개")
        log("\n--- 샘플 (5개) ---")

        for i, prod in enumerate(products[:5], 1):
            log(f"{i}. {prod.get('prodName', 'N/A')}")
            log(f"   ProdCode: {prod.get('onlineProdCode', 'N/A')}")
            log(f"   가격: {prod.get('price', 0):,} → {prod.get('salePrice', 0):,}원")
            log(f"   카테고리: {prod.get('mainCategory', 'N/A')} > {prod.get('subCategory', 'N/A')}")
            log(f"   리뷰: {prod.get('reviewCount', 0)}개, 평점: {prod.get('avgRating', 0)}")
            log("")

        return products

    except Exception as e:
        log(f"테스트 오류: {e}")
        import traceback
        log(traceback.format_exc())
        return []

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "full":
            crawl_all(test_mode=False, get_details=True)
        elif sys.argv[1] == "test":
            crawl_all(test_mode=True, get_details=True)
        elif sys.argv[1] == "links":
            # 링크만 수집 (빠름)
            crawl_all(test_mode=False, get_details=False)
        else:
            quick_test()
    else:
        quick_test()
