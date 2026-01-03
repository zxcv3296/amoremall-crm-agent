# -*- coding: utf-8 -*-
"""
리뷰 데이터 수정 스크립트
1. 불필요한 브랜드 제거 (정글몬스터, 아모스 프로페셔널, 라 리베라)
2. 누락된 브랜드 크롤링 (려, 미쟝센, 바이탈뷰티, 오딧세이)
3. 합치기
"""

import json
import time
import os
from datetime import datetime
from typing import List, Dict

# 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
REVIEWS_FILE = os.path.join(DATA_DIR, "crawled_reviews.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "crawled_products.json")

# 제거할 브랜드
REMOVE_BRANDS = ["정글몬스터", "아모스 프로페셔널", "라 리베라"]

# 추가할 브랜드
ADD_BRANDS = ["려", "미쟝센", "바이탈뷰티", "오딧세이"]


def log(msg: str):
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    except UnicodeEncodeError:
        # 인코딩 에러 시 ASCII로 대체
        safe_msg = msg.encode('ascii', 'replace').decode('ascii')
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {safe_msg}")


def remove_brands():
    """불필요한 브랜드 제거"""
    log("=" * 60)
    log("Step 1: 불필요한 브랜드 제거")
    log("=" * 60)

    with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_count = len(data["brands"])
    log(f"원본 브랜드 수: {original_count}")

    # 브랜드 필터링
    data["brands"] = [b for b in data["brands"] if b["brandName"] not in REMOVE_BRANDS]

    new_count = len(data["brands"])
    log(f"제거 후 브랜드 수: {new_count}")
    log(f"제거된 브랜드: {REMOVE_BRANDS}")

    # 저장
    with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log("저장 완료!")
    return data


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

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver


def scroll_and_collect_reviews(driver, prod_sn: int, max_reviews: int = 50) -> List[Dict]:
    """스크롤하며 리뷰 수집"""
    from selenium.webdriver.common.by import By

    url = f"https://www.amoremall.com/kr/ko/product/detail?onlineProdSn={prod_sn}"
    driver.get(url)
    time.sleep(3)

    # 리뷰 섹션까지 스크롤
    for _ in range(10):
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(0.3)

    time.sleep(2)

    # 리뷰 탭 클릭
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

    # 리뷰 수집
    reviews = []
    seen_texts = set()

    for _ in range(10):
        elements = driver.find_elements(By.CSS_SELECTOR, "[class*='Review'] p, [class*='review'] p")

        for elem in elements:
            try:
                text = elem.text.strip()
                if text and len(text) > 20 and text not in seen_texts:
                    seen_texts.add(text)
                    reviews.append({
                        "content": text,
                        "onlineProdSn": prod_sn
                    })
            except:
                pass

        if len(reviews) >= max_reviews:
            break

        # 더보기 버튼 클릭
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


def crawl_brand_reviews(driver, brand_name: str, products: List[Dict], reviews_per_product: int = 30) -> Dict:
    """브랜드 리뷰 크롤링"""
    log(f"\n  [{brand_name}] 크롤링 시작 ({len(products)}개 상품)")

    brand_reviews = {
        "brandName": brand_name,
        "productCount": len(products),
        "totalReviews": 0,
        "reviews": []
    }

    # 리뷰가 많은 상품 우선
    sorted_products = sorted(products, key=lambda x: x.get("reviewCount", 0), reverse=True)

    for i, prod in enumerate(sorted_products[:20]):
        prod_sn = prod.get("onlineProdSn")
        prod_name = prod.get("prodName", "")
        review_count = prod.get("reviewCount", 0)

        if review_count == 0:
            continue

        log(f"    [{i+1}] {prod_name[:25]}... (리뷰 {review_count}개)")

        try:
            reviews = scroll_and_collect_reviews(driver, prod_sn, max_reviews=reviews_per_product)

            for review in reviews:
                review["prodName"] = prod_name
                review["brandName"] = brand_name

            brand_reviews["reviews"].extend(reviews)
            log(f"        -> {len(reviews)}개 수집")

        except Exception as e:
            log(f"        -> 오류: {e}")

        time.sleep(1)

    brand_reviews["totalReviews"] = len(brand_reviews["reviews"])
    log(f"  [{brand_name}] 총 {brand_reviews['totalReviews']}개 리뷰")

    return brand_reviews


def crawl_missing_brands():
    """누락된 브랜드 크롤링"""
    log("\n" + "=" * 60)
    log("Step 2: 누락된 브랜드 크롤링")
    log("=" * 60)

    # 상품 데이터 로드
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        products_data = json.load(f)

    products = products_data.get("products", [])

    # 브랜드별 그룹화
    brand_products = {}
    for prod in products:
        brand = prod.get("brandName", "")
        if brand in ADD_BRANDS:
            if brand not in brand_products:
                brand_products[brand] = []
            brand_products[brand].append(prod)

    log(f"크롤링할 브랜드: {list(brand_products.keys())}")

    driver = None
    new_brands = []

    try:
        driver = setup_driver()
        log("WebDriver 초기화 완료")

        for brand_name in ADD_BRANDS:
            if brand_name in brand_products:
                brand_reviews = crawl_brand_reviews(
                    driver,
                    brand_name,
                    brand_products[brand_name],
                    reviews_per_product=30
                )
                new_brands.append(brand_reviews)
            else:
                log(f"  [{brand_name}] 상품 없음, 건너뜀")

            time.sleep(2)

    except Exception as e:
        log(f"크롤링 오류: {e}")
        import traceback
        log(traceback.format_exc())

    finally:
        if driver:
            driver.quit()
            log("WebDriver 종료")

    return new_brands


def merge_reviews(new_brands: List[Dict]):
    """리뷰 데이터 합치기"""
    log("\n" + "=" * 60)
    log("Step 3: 리뷰 데이터 합치기")
    log("=" * 60)

    with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    log(f"기존 브랜드 수: {len(data['brands'])}")

    # 새 브랜드 추가
    data["brands"].extend(new_brands)
    data["crawled_at"] = datetime.now().isoformat()

    log(f"추가된 브랜드: {[b['brandName'] for b in new_brands]}")
    log(f"최종 브랜드 수: {len(data['brands'])}")

    # 저장
    with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log("저장 완료!")

    # 최종 확인
    log("\n" + "=" * 60)
    log("최종 브랜드 목록")
    log("=" * 60)
    for b in sorted(data["brands"], key=lambda x: x["brandName"]):
        log(f"  - {b['brandName']}: {b['totalReviews']}개 리뷰")


def main():
    log("=" * 60)
    log("리뷰 데이터 수정 시작")
    log("=" * 60)

    # Step 1: 불필요한 브랜드 제거 (이미 완료됨, 스킵)
    # remove_brands()

    # Step 2: 누락된 브랜드 크롤링
    new_brands = crawl_missing_brands()

    # Step 3: 합치기
    if new_brands:
        merge_reviews(new_brands)
    else:
        log("새로 크롤링된 브랜드가 없습니다.")

    log("\n" + "=" * 60)
    log("완료!")
    log("=" * 60)


if __name__ == "__main__":
    main()
