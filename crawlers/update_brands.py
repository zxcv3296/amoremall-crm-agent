# -*- coding: utf-8 -*-
"""
브랜드 업데이트 스크립트
1. 3개 브랜드 제거 (정글몬스터, 아모스 프로페셔널, 라 리베라)
2. 4개 브랜드 크롤링 (려, 미쟝센, 바이탈뷰티, 오딧세이)
3. 결과 합치기
"""

import json
import re
import time
import os
from datetime import datetime
from typing import List, Dict

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "crawled_products.json")
REVIEWS_FILE = os.path.join(DATA_DIR, "crawled_reviews.json")

# 제거할 브랜드
BRANDS_TO_REMOVE = ["정글몬스터", "아모스 프로페셔널", "라 리베라"]

# 크롤링할 브랜드
TARGET_BRANDS = [
    {"brandSn": 23, "brandName": "려"},
    {"brandSn": 9, "brandName": "미쟝센"},
    {"brandSn": 234, "brandName": "바이탈뷰티"},
    {"brandSn": 96, "brandName": "오딧세이"},
]

BRAND_ALL_URL = "https://www.amoremall.com/kr/ko/display/brand/detail/all?brandSn={brand_sn}&sort=Bestselling"


def log(msg: str):
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)
    except UnicodeEncodeError:
        safe_msg = msg.encode('ascii', 'replace').decode('ascii')
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {safe_msg}", flush=True)


def remove_brands():
    """3개 브랜드 제거"""
    log("=" * 60)
    log("1단계: 브랜드 제거")
    log(f"제거 대상: {BRANDS_TO_REMOVE}")
    log("=" * 60)

    # Products 파일 처리
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        products_data = json.load(f)

    original_count = len(products_data["products"])
    products_data["products"] = [
        p for p in products_data["products"]
        if p.get("brandName") not in BRANDS_TO_REMOVE
    ]
    products_data["brands"] = [
        b for b in products_data.get("brands", [])
        if b.get("brandName") not in BRANDS_TO_REMOVE
    ]
    products_data["product_count"] = len(products_data["products"])
    products_data["brand_count"] = len(products_data["brands"])

    removed_products = original_count - len(products_data["products"])
    log(f"Products: {original_count} -> {len(products_data['products'])} (제거: {removed_products})")

    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products_data, f, ensure_ascii=False, indent=2)

    # Reviews 파일 처리
    with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
        reviews_data = json.load(f)

    original_brands = len(reviews_data["brands"])
    reviews_data["brands"] = [
        b for b in reviews_data["brands"]
        if b.get("brandName") not in BRANDS_TO_REMOVE
    ]

    removed_brands = original_brands - len(reviews_data["brands"])
    log(f"Reviews: {original_brands} -> {len(reviews_data['brands'])} 브랜드 (제거: {removed_brands})")

    with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(reviews_data, f, ensure_ascii=False, indent=2)

    log("브랜드 제거 완료!")
    return True


def setup_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver


def get_product_links(driver, brand_sn: int, brand_name: str, max_scrolls: int = 50) -> List[Dict]:
    """브랜드 페이지에서 상품 링크 추출"""
    log(f"  [{brand_name}] 상품 링크 수집 중...")

    url = BRAND_ALL_URL.format(brand_sn=brand_sn)
    driver.get(url)
    time.sleep(3)

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

    products = []
    seen = set()
    links = driver.find_elements("css selector", "a[href*='/product/detail']")

    for link in links:
        try:
            href = link.get_attribute("href")
            if not href:
                continue

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

                try:
                    parent = link.find_element("xpath", "./..")
                    text = parent.text
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    if lines:
                        for line in lines:
                            if not re.match(r'^[\d,]+원?$', line) and not re.match(r'^\d+%$', line):
                                prod["prodName"] = line
                                break
                    price_match = re.search(r'([\d,]+)원', text)
                    if price_match:
                        prod["salePrice"] = int(price_match.group(1).replace(',', ''))
                except:
                    pass

                products.append(prod)
        except:
            continue

    log(f"  [{brand_name}] {len(products)}개 상품 링크 수집")
    return products


def get_product_detail(driver, prod: Dict) -> Dict:
    """상품 상세 정보"""
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
            page_props = data.get("props", {}).get("pageProps", {})
            initial_state = page_props.get("initialState", {})

            if isinstance(initial_state, str):
                initial_state = json.loads(initial_state)

            prod_detail = initial_state.get("productDetail", {})
            prod_info = prod_detail.get("productInfo", {})

            if prod_info:
                prod["prodName"] = prod_info.get("onlineProdName") or prod.get("prodName", "")

                # 카테고리 정보
                cat_info = prod_info.get("categoryInfo", {})
                cat_group = cat_info.get("categoryGroupInfo", {})
                if cat_group:
                    prod["mainCategory"] = cat_group.get("large", "")
                    prod["subCategory"] = cat_group.get("middle", "")
                    prod["detailCategory"] = cat_group.get("small", "")

                review_info = prod_info.get("reviewInfo", {})
                if review_info:
                    prod["reviewCount"] = review_info.get("reviewCount", 0)
                    prod["avgRating"] = round(review_info.get("reviewScope", 0), 2)

                online_price = prod_info.get("onlinePriceInfo", {})
                price_data = online_price.get("priceInfo", {})
                if price_data:
                    prod["price"] = price_data.get("beforeSalePrice", 0)
                    prod["salePrice"] = price_data.get("discountedPrice", 0) or price_data.get("beforeSalePrice", 0)
                    prod["discountRate"] = price_data.get("discountRate", 0)

                # 이미지
                online_images = prod_info.get("onlineImages", [])
                if online_images:
                    prod["imageUrl"] = online_images[0].get("imgUrl", "")

    except Exception as e:
        pass

    return prod


def scroll_and_collect_reviews(driver, prod_sn: int, max_reviews: int = 50) -> List[Dict]:
    """리뷰 수집"""
    from selenium.webdriver.common.by import By

    url = f"https://www.amoremall.com/kr/ko/product/detail?onlineProdSn={prod_sn}"
    driver.get(url)
    time.sleep(3)

    for _ in range(10):
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(0.3)
    time.sleep(2)

    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, "button")
        for btn in buttons:
            try:
                if '리뷰' in btn.text:
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)
                    break
            except:
                pass
    except:
        pass

    reviews = []
    seen_texts = set()

    for _ in range(10):
        elements = driver.find_elements(By.CSS_SELECTOR, "[class*='Review'] p, [class*='review'] p")
        for elem in elements:
            try:
                text = elem.text.strip()
                if text and len(text) > 20 and text not in seen_texts:
                    seen_texts.add(text)
                    reviews.append({"content": text, "onlineProdSn": prod_sn})
            except:
                pass

        if len(reviews) >= max_reviews:
            break

        try:
            more_btns = driver.find_elements(By.CSS_SELECTOR, "[class*='more'], [class*='More'] button")
            clicked = False
            for btn in more_btns:
                if '더보기' in btn.text or 'more' in btn.text.lower():
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    clicked = True
                    break
            if not clicked:
                break
        except:
            break

    return reviews[:max_reviews]


def crawl_brand_products_and_reviews(driver, brand: Dict) -> tuple:
    """브랜드 상품+리뷰 크롤링"""
    brand_sn = brand["brandSn"]
    brand_name = brand["brandName"]

    log(f"\n{'='*60}")
    log(f"[{brand_name}] 크롤링 시작")
    log(f"{'='*60}")

    # 1. 상품 수집
    products = get_product_links(driver, brand_sn, brand_name)

    # 2. 상세 정보 수집
    log(f"  [{brand_name}] 상세 정보 수집 중...")
    for i, prod in enumerate(products):
        prod = get_product_detail(driver, prod)
        products[i] = prod
        if (i + 1) % 10 == 0:
            log(f"    {i+1}/{len(products)} 완료")
        time.sleep(0.5)

    # 3. 리뷰 수집
    log(f"  [{brand_name}] 리뷰 수집 중...")
    brand_reviews = {
        "brandName": brand_name,
        "productCount": len(products),
        "totalReviews": 0,
        "reviews": []
    }

    sorted_products = sorted(products, key=lambda x: x.get("reviewCount", 0), reverse=True)

    for i, prod in enumerate(sorted_products[:20]):
        prod_sn = prod.get("onlineProdSn")
        prod_name = prod.get("prodName", "")
        review_count = prod.get("reviewCount", 0)

        if review_count == 0:
            continue

        log(f"    [{i+1}] {prod_name[:25]}... (리뷰 {review_count}개)")

        try:
            reviews = scroll_and_collect_reviews(driver, prod_sn, max_reviews=30)
            for review in reviews:
                review["prodName"] = prod_name
                review["brandName"] = brand_name
            brand_reviews["reviews"].extend(reviews)
            log(f"        -> {len(reviews)}개 수집")
        except Exception as e:
            log(f"        -> 오류: {e}")

        time.sleep(1)

    brand_reviews["totalReviews"] = len(brand_reviews["reviews"])
    log(f"  [{brand_name}] 총 {len(products)}개 상품, {brand_reviews['totalReviews']}개 리뷰")

    return products, brand_reviews


def crawl_target_brands():
    """4개 브랜드 크롤링"""
    log("\n" + "=" * 60)
    log("2단계: 4개 브랜드 크롤링")
    log(f"대상: {[b['brandName'] for b in TARGET_BRANDS]}")
    log("=" * 60)

    driver = None
    all_new_products = []
    all_new_reviews = []

    try:
        driver = setup_driver()
        log("WebDriver 초기화 완료")

        for brand in TARGET_BRANDS:
            products, reviews = crawl_brand_products_and_reviews(driver, brand)
            all_new_products.extend(products)
            all_new_reviews.append(reviews)
            time.sleep(2)

    except Exception as e:
        log(f"크롤링 오류: {e}")
        import traceback
        log(traceback.format_exc())

    finally:
        if driver:
            driver.quit()
            log("WebDriver 종료")

    return all_new_products, all_new_reviews


def merge_results(new_products, new_reviews):
    """크롤링 결과 합치기"""
    log("\n" + "=" * 60)
    log("3단계: 결과 합치기")
    log("=" * 60)

    # Products 파일 업데이트
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        products_data = json.load(f)

    # 기존에 해당 브랜드 상품이 있으면 제거 (중복 방지)
    target_brand_names = [b["brandName"] for b in TARGET_BRANDS]
    products_data["products"] = [
        p for p in products_data["products"]
        if p.get("brandName") not in target_brand_names
    ]

    # 새 상품 추가
    products_data["products"].extend(new_products)
    products_data["product_count"] = len(products_data["products"])

    # 브랜드 목록 업데이트
    existing_brand_names = [b["brandName"] for b in products_data.get("brands", [])]
    for brand in TARGET_BRANDS:
        if brand["brandName"] not in existing_brand_names:
            products_data["brands"].append(brand)
    products_data["brand_count"] = len(products_data["brands"])
    products_data["crawled_at"] = datetime.now().isoformat()

    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products_data, f, ensure_ascii=False, indent=2)

    log(f"Products 저장 완료: 총 {len(products_data['products'])}개 (+{len(new_products)}개)")

    # Reviews 파일 업데이트
    with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
        reviews_data = json.load(f)

    # 기존에 해당 브랜드 리뷰가 있으면 제거 (중복 방지)
    reviews_data["brands"] = [
        b for b in reviews_data["brands"]
        if b.get("brandName") not in target_brand_names
    ]

    # 새 리뷰 추가
    reviews_data["brands"].extend(new_reviews)
    reviews_data["crawled_at"] = datetime.now().isoformat()

    with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(reviews_data, f, ensure_ascii=False, indent=2)

    total_new_reviews = sum(r["totalReviews"] for r in new_reviews)
    log(f"Reviews 저장 완료: 총 {len(reviews_data['brands'])}개 브랜드 (+{len(new_reviews)}개)")
    log(f"새 리뷰 수: {total_new_reviews}개")


def main():
    log("=" * 60)
    log("브랜드 업데이트 시작")
    log("=" * 60)

    # 1. 브랜드 제거
    remove_brands()

    # 2. 크롤링
    new_products, new_reviews = crawl_target_brands()

    # 3. 결과 합치기
    if new_products:
        merge_results(new_products, new_reviews)

    # 최종 확인
    log("\n" + "=" * 60)
    log("완료!")
    log("=" * 60)

    for brand in TARGET_BRANDS:
        brand_name = brand["brandName"]
        prods = [p for p in new_products if p["brandName"] == brand_name]
        revs = [r for r in new_reviews if r["brandName"] == brand_name]
        rev_count = revs[0]["totalReviews"] if revs else 0
        log(f"  - {brand_name}: {len(prods)}개 상품, {rev_count}개 리뷰")


if __name__ == "__main__":
    main()
