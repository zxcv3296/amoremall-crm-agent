# -*- coding: utf-8 -*-
"""
아모레몰 리뷰 크롤러
==============================
- 브랜드별 상품 리뷰 크롤링
- 브랜드 특성 분석을 위한 리뷰 텍스트 수집
- API: api-gw.amoremall.com
"""

import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional

# 저장 경로
SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
REVIEW_FILE = os.path.join(SAVE_DIR, "crawled_reviews.json")
PRODUCTS_FILE = os.path.join(SAVE_DIR, "crawled_products.json")
LOG_FILE = os.path.join(SAVE_DIR, "review_crawl_log.txt")

# API 엔드포인트
REVIEW_API = "https://api-gw.amoremall.com/commune/v2/M01/apcp/reviews"
REVIEW_SUMMARY_API = "https://api-gw.amoremall.com/ecp/v1/M01/sales/reviews/summaryEx"


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
    """Selenium WebDriver 설정 (API 호출용)"""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver


def get_reviews_via_page(driver, prod_sn: int, max_reviews: int = 100) -> List[Dict]:
    """
    상품 페이지에서 리뷰 크롤링
    - 페이지 접근 후 API 호출 캡처
    """
    from selenium.webdriver.common.by import By

    url = f"https://www.amoremall.com/kr/ko/product/detail?onlineProdSn={prod_sn}"
    driver.get(url)
    time.sleep(3)

    # 스크롤하여 리뷰 로드
    for _ in range(5):
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(0.5)

    # 리뷰 탭 클릭 시도
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, "button")
        for btn in buttons:
            if '리뷰' in btn.text:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
                break
    except:
        pass

    # 리뷰 요소 추출
    reviews = []
    review_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='ReviewItem'], [class*='review-item']")

    for elem in review_elements[:max_reviews]:
        try:
            text = elem.text
            if text and len(text) > 10:
                reviews.append({
                    "content": text,
                    "onlineProdSn": prod_sn
                })
        except:
            pass

    return reviews


def get_reviews_from_dom(driver, prod_sn: int) -> List[Dict]:
    """DOM에서 리뷰 텍스트 추출"""
    from selenium.webdriver.common.by import By

    reviews = []

    # 다양한 리뷰 선택자 시도
    selectors = [
        "[class*='ReviewContent'] p",
        "[class*='review-content'] p",
        "[class*='ReviewItem'] p",
        "[class*='review_text']",
        ".review-body p"
    ]

    for sel in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, sel)
        for elem in elements:
            try:
                text = elem.text.strip()
                if text and len(text) > 20:
                    reviews.append({
                        "content": text,
                        "onlineProdSn": prod_sn
                    })
            except:
                pass

    return reviews


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

    # 리뷰 "더보기" 버튼 클릭하며 수집
    reviews = []
    seen_texts = set()

    for _ in range(10):  # 최대 10번 더보기
        # 현재 리뷰 수집
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
            more_btns = driver.find_elements(By.CSS_SELECTOR, "[class*='more'], [class*='More'] button, button[class*='load']")
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
    """브랜드별 리뷰 크롤링"""
    log(f"\n[{brand_name}] 리뷰 크롤링 시작 ({len(products)}개 상품)")

    brand_reviews = {
        "brandName": brand_name,
        "productCount": len(products),
        "totalReviews": 0,
        "reviews": []
    }

    # 리뷰가 많은 상품 우선 정렬
    sorted_products = sorted(products, key=lambda x: x.get("reviewCount", 0), reverse=True)

    for i, prod in enumerate(sorted_products[:20]):  # 상위 20개 상품
        prod_sn = prod.get("onlineProdSn")
        prod_name = prod.get("prodName", "")
        review_count = prod.get("reviewCount", 0)

        if review_count == 0:
            continue

        log(f"  [{i+1}] {prod_name[:30]}... (리뷰 {review_count}개)")

        try:
            reviews = scroll_and_collect_reviews(driver, prod_sn, max_reviews=reviews_per_product)

            for review in reviews:
                review["prodName"] = prod_name
                review["brandName"] = brand_name

            brand_reviews["reviews"].extend(reviews)
            log(f"      -> {len(reviews)}개 수집")

        except Exception as e:
            log(f"      -> 오류: {e}")

        time.sleep(1)

    brand_reviews["totalReviews"] = len(brand_reviews["reviews"])
    log(f"  [{brand_name}] 총 {brand_reviews['totalReviews']}개 리뷰 수집")

    return brand_reviews


def crawl_all_reviews(max_brands: int = None, reviews_per_product: int = 30):
    """전체 브랜드 리뷰 크롤링"""
    log("=" * 60)
    log("아모레몰 리뷰 크롤링 시작")
    log("=" * 60)

    # 상품 데이터 로드
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    products = data.get("products", [])
    log(f"총 {len(products)}개 상품 로드")

    # 브랜드별 그룹화
    brands = {}
    for prod in products:
        brand = prod.get("brandName", "Unknown")
        if brand not in brands:
            brands[brand] = []
        brands[brand].append(prod)

    log(f"총 {len(brands)}개 브랜드")

    driver = None
    all_reviews = {
        "crawled_at": datetime.now().isoformat(),
        "brands": []
    }

    try:
        driver = setup_driver()
        log("WebDriver 초기화 완료")

        brand_list = list(brands.items())
        if max_brands:
            brand_list = brand_list[:max_brands]

        for i, (brand_name, brand_products) in enumerate(brand_list, 1):
            log(f"\n[{i}/{len(brand_list)}] {brand_name}")

            try:
                brand_reviews = crawl_brand_reviews(
                    driver,
                    brand_name,
                    brand_products,
                    reviews_per_product=reviews_per_product
                )
                all_reviews["brands"].append(brand_reviews)

            except Exception as e:
                log(f"  오류: {e}")

            # 중간 저장
            if i % 5 == 0:
                with open(REVIEW_FILE, "w", encoding="utf-8") as f:
                    json.dump(all_reviews, f, ensure_ascii=False, indent=2)
                log(f"  (중간 저장 완료)")

            time.sleep(2)

    except Exception as e:
        log(f"크롤링 오류: {e}")
        import traceback
        log(traceback.format_exc())

    finally:
        if driver:
            driver.quit()
            log("WebDriver 종료")

    # 최종 저장
    with open(REVIEW_FILE, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)

    # 통계
    total_reviews = sum(b["totalReviews"] for b in all_reviews["brands"])
    log(f"\n총 {total_reviews}개 리뷰 수집")
    log(f"저장 완료: {REVIEW_FILE}")
    log("=" * 60)
    log("크롤링 완료!")
    log("=" * 60)

    return all_reviews


def quick_test():
    """빠른 테스트 (1개 브랜드)"""
    log("=" * 60)
    log("리뷰 크롤링 테스트")
    log("=" * 60)

    driver = None
    try:
        driver = setup_driver()
        log("WebDriver 초기화 완료")

        # 설화수 상품 중 리뷰 많은 것
        prod_sn = 17937  # 해피바스

        log(f"\n테스트 상품: {prod_sn}")
        reviews = scroll_and_collect_reviews(driver, prod_sn, max_reviews=10)

        log(f"\n수집된 리뷰: {len(reviews)}개")
        for i, r in enumerate(reviews[:5], 1):
            log(f"\n[리뷰 {i}]")
            log(r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"])

    except Exception as e:
        log(f"오류: {e}")
        import traceback
        log(traceback.format_exc())

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "full":
            crawl_all_reviews(reviews_per_product=30)
        elif sys.argv[1] == "test":
            crawl_all_reviews(max_brands=2, reviews_per_product=10)
        else:
            quick_test()
    else:
        quick_test()
