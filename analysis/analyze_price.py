"""
가격 데이터 기반 브랜드 특성 분석
"""
import json
import os
import numpy as np

# 데이터는 data 폴더에 위치
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PRODUCT_FILE = os.path.join(DATA_DIR, "crawled_products.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "price_analysis.json")

def load_products():
    with open(PRODUCT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_brand_prices(products):
    """브랜드별 가격 분석"""
    brand_prices = {}

    for product in products:
        brand_name = product.get('brandName', 'Unknown')
        sale_price = product.get('salePrice', 0)
        original_price = product.get('price', 0)
        discount_rate = product.get('discountRate', 0)

        if brand_name not in brand_prices:
            brand_prices[brand_name] = {
                'prices': [],
                'original_prices': [],
                'discount_rates': []
            }

        if sale_price > 0:
            brand_prices[brand_name]['prices'].append(sale_price)
        if original_price > 0:
            brand_prices[brand_name]['original_prices'].append(original_price)
        if discount_rate > 0:
            brand_prices[brand_name]['discount_rates'].append(discount_rate)

    return brand_prices

def calculate_price_score(avg_price, all_avg_prices):
    """
    가격 기반 Mass/Premium 점수 계산
    전체 평균 대비 상대적 위치를 -100 ~ +100 스케일로 변환
    """
    min_price = min(all_avg_prices)
    max_price = max(all_avg_prices)
    median_price = np.median(all_avg_prices)

    if max_price == min_price:
        return 0

    # 중앙값 기준으로 정규화 (-100 ~ +100)
    if avg_price >= median_price:
        score = ((avg_price - median_price) / (max_price - median_price)) * 100
    else:
        score = ((avg_price - median_price) / (median_price - min_price)) * 100

    return min(100, max(-100, score))

def main():
    print("=" * 60)
    print("가격 데이터 분석 시작")
    print("=" * 60)

    data = load_products()
    products = data.get('products', [])

    print(f"총 {len(products)}개 상품 분석\n")

    brand_prices = analyze_brand_prices(products)

    # 브랜드별 평균 가격 계산
    results = {}
    all_avg_prices = []

    for brand_name, price_data in brand_prices.items():
        if not price_data['prices']:
            continue

        avg_price = np.mean(price_data['prices'])
        all_avg_prices.append(avg_price)

    # 점수 계산
    for brand_name, price_data in brand_prices.items():
        if not price_data['prices']:
            continue

        prices = price_data['prices']
        avg_price = np.mean(prices)
        median_price = np.median(prices)
        min_price = min(prices)
        max_price = max(prices)
        avg_discount = np.mean(price_data['discount_rates']) if price_data['discount_rates'] else 0

        price_score = calculate_price_score(avg_price, all_avg_prices)

        results[brand_name] = {
            'product_count': len(prices),
            'avg_price': round(avg_price),
            'median_price': round(median_price),
            'min_price': round(min_price),
            'max_price': round(max_price),
            'avg_discount_rate': round(avg_discount, 1),
            'price_score': round(price_score, 1)  # -100(Mass) ~ +100(Premium)
        }

        print(f"[{brand_name}]")
        print(f"  평균가: {avg_price:,.0f}원 | 중앙값: {median_price:,.0f}원")
        print(f"  범위: {min_price:,.0f} ~ {max_price:,.0f}원")
        print(f"  가격 점수: {price_score:+.1f}")
        print()

    # 전체 통계
    print("=" * 60)
    print("전체 가격 분포")
    print("=" * 60)
    print(f"전체 평균: {np.mean(all_avg_prices):,.0f}원")
    print(f"전체 중앙값: {np.median(all_avg_prices):,.0f}원")
    print(f"최저 평균 브랜드: {min(results.items(), key=lambda x: x[1]['avg_price'])}")
    print(f"최고 평균 브랜드: {max(results.items(), key=lambda x: x[1]['avg_price'])}")

    # 결과 저장
    output = {
        "analyzed_at": data.get('crawled_at'),
        "method": "price_analysis",
        "overall_stats": {
            "avg_price": round(np.mean(all_avg_prices)),
            "median_price": round(np.median(all_avg_prices)),
            "min_avg": round(min(all_avg_prices)),
            "max_avg": round(max(all_avg_prices))
        },
        "brands": results
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUTPUT_FILE}")

    # 가격 순위
    print("\n## 브랜드 가격 순위 (높은 순)\n")
    sorted_brands = sorted(results.items(), key=lambda x: x[1]['avg_price'], reverse=True)
    for i, (brand, data) in enumerate(sorted_brands, 1):
        print(f"{i:2}. {brand:<15} 평균 {data['avg_price']:>8,}원  점수: {data['price_score']:>+6.1f}")

if __name__ == "__main__":
    main()
