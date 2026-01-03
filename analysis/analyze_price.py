"""
가격 데이터 기반 브랜드 특성 분석
- 하이브리드 카테고리 정규화 (v3)
- subCategory 10개 이상 → sub 기준, 미만 → main 기준
- 스케일: -50 ~ +50 (다른 축과 균형)
"""
import json
import os
import numpy as np

# 데이터는 data 폴더에 위치
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PRODUCT_FILE = os.path.join(DATA_DIR, "crawled_products.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "price_analysis.json")

# 하이브리드 정규화 임계값
MIN_SUBCATEGORY_COUNT = 10


def load_products():
    with open(PRODUCT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_category_price_stats(products):
    """mainCategory와 subCategory 모두에 대한 가격 통계 계산"""
    main_prices = {}
    sub_prices = {}

    for product in products:
        main_cat = product.get('mainCategory', 'Unknown')
        sub_cat = product.get('subCategory', '')
        sale_price = product.get('salePrice', 0)

        if sale_price <= 0:
            continue

        # mainCategory 통계
        if main_cat not in main_prices:
            main_prices[main_cat] = []
        main_prices[main_cat].append(sale_price)

        # subCategory 통계 (main + sub 조합으로 키 생성)
        if sub_cat:
            sub_key = f"{main_cat}|{sub_cat}"
            if sub_key not in sub_prices:
                sub_prices[sub_key] = []
            sub_prices[sub_key].append(sale_price)

    # 통계 계산
    def calc_stats(prices_dict):
        stats = {}
        for cat, prices in prices_dict.items():
            stats[cat] = {
                'min': min(prices),
                'max': max(prices),
                'median': np.median(prices),
                'mean': np.mean(prices),
                'count': len(prices)
            }
        return stats

    return calc_stats(main_prices), calc_stats(sub_prices)


def normalize_price_hybrid(price, main_cat, sub_cat, main_stats, sub_stats):
    """
    하이브리드 정규화:
    - subCategory 상품 10개 이상 → subCategory 기준
    - 10개 미만 → mainCategory 기준
    반환값: 0 ~ 1
    """
    # subCategory 키 생성
    sub_key = f"{main_cat}|{sub_cat}" if sub_cat else None

    # subCategory 사용 가능 여부 확인
    use_sub = (
        sub_key and
        sub_key in sub_stats and
        sub_stats[sub_key]['count'] >= MIN_SUBCATEGORY_COUNT
    )

    if use_sub:
        stats = sub_stats[sub_key]
    elif main_cat in main_stats:
        stats = main_stats[main_cat]
    else:
        return 0.5  # 카테고리 없으면 중간값

    min_price = stats['min']
    max_price = stats['max']

    if max_price == min_price:
        return 0.5

    normalized = (price - min_price) / (max_price - min_price)
    return min(1.0, max(0.0, normalized))


def analyze_brand_prices_hybrid(products, main_stats, sub_stats):
    """브랜드별 하이브리드 카테고리 가격 분석"""
    brand_data = {}

    for product in products:
        brand_name = product.get('brandName', 'Unknown')
        main_cat = product.get('mainCategory', 'Unknown')
        sub_cat = product.get('subCategory', '')
        sale_price = product.get('salePrice', 0)
        original_price = product.get('price', 0)
        discount_rate = product.get('discountRate', 0)

        if sale_price <= 0:
            continue

        if brand_name not in brand_data:
            brand_data[brand_name] = {
                'prices': [],
                'original_prices': [],
                'discount_rates': [],
                'normalized_scores': [],
                'normalization_method': [],  # 'sub' or 'main' 기록
                'categories': []
            }

        # 하이브리드 정규화 점수 계산
        norm_score = normalize_price_hybrid(sale_price, main_cat, sub_cat, main_stats, sub_stats)

        # 어떤 기준으로 정규화했는지 기록
        sub_key = f"{main_cat}|{sub_cat}" if sub_cat else None
        used_sub = (
            sub_key and
            sub_key in sub_stats and
            sub_stats[sub_key]['count'] >= MIN_SUBCATEGORY_COUNT
        )

        brand_data[brand_name]['prices'].append(sale_price)
        brand_data[brand_name]['normalized_scores'].append(norm_score)
        brand_data[brand_name]['normalization_method'].append('sub' if used_sub else 'main')
        brand_data[brand_name]['categories'].append(f"{main_cat} > {sub_cat}" if sub_cat else main_cat)

        if original_price > 0:
            brand_data[brand_name]['original_prices'].append(original_price)
        if discount_rate > 0:
            brand_data[brand_name]['discount_rates'].append(discount_rate)

    return brand_data


def calculate_hybrid_score(brand_data):
    """
    하이브리드 정규화 점수의 평균을 -50 ~ +50 스케일로 변환
    0.5 = 0점 (카테고리 중간)
    1.0 = +50점 (카테고리 내 최고가)
    0.0 = -50점 (카테고리 내 최저가)
    """
    if not brand_data['normalized_scores']:
        return 0

    avg_norm = np.mean(brand_data['normalized_scores'])
    # 0~1을 -50~+50으로 변환
    score = (avg_norm - 0.5) * 100
    return min(50, max(-50, score))


def main():
    print("=" * 60)
    print("가격 데이터 분석 (하이브리드 정규화 v3)")
    print("=" * 60)

    data = load_products()
    products = data.get('products', [])

    print(f"총 {len(products)}개 상품 분석\n")

    # 1. mainCategory + subCategory 통계 계산
    main_stats, sub_stats = get_category_price_stats(products)

    print("=" * 60)
    print("mainCategory 가격 범위")
    print("=" * 60)
    for cat, stats in sorted(main_stats.items(), key=lambda x: x[1]['mean'], reverse=True):
        print(f"  {cat}: {stats['min']:,}원 ~ {stats['max']:,}원 (평균 {stats['mean']:,.0f}원, {stats['count']}개)")

    print()
    print("=" * 60)
    print(f"subCategory 정규화 사용 기준: {MIN_SUBCATEGORY_COUNT}개 이상")
    print("=" * 60)
    usable_subs = [(k, v) for k, v in sub_stats.items() if v['count'] >= MIN_SUBCATEGORY_COUNT]
    print(f"  사용 가능한 subCategory: {len(usable_subs)}개")
    for sub_key, stats in sorted(usable_subs, key=lambda x: -x[1]['count'])[:10]:
        print(f"    {sub_key}: {stats['count']}개 ({stats['min']:,} ~ {stats['max']:,}원)")
    print()

    # 2. 브랜드별 하이브리드 분석
    brand_data = analyze_brand_prices_hybrid(products, main_stats, sub_stats)

    # 3. 결과 계산
    results = {}
    all_scores = []

    for brand_name, data_item in brand_data.items():
        if not data_item['prices']:
            continue

        prices = data_item['prices']
        avg_price = np.mean(prices)
        median_price = np.median(prices)
        min_price = min(prices)
        max_price = max(prices)
        avg_discount = np.mean(data_item['discount_rates']) if data_item['discount_rates'] else 0

        # 하이브리드 정규화 점수 (-50 ~ +50)
        hybrid_score = calculate_hybrid_score(data_item)
        all_scores.append(hybrid_score)

        # 정규화 방법 분포
        method_dist = {}
        for m in data_item['normalization_method']:
            method_dist[m] = method_dist.get(m, 0) + 1
        sub_ratio = method_dist.get('sub', 0) / len(data_item['normalization_method']) * 100

        # 카테고리 분포
        category_dist = {}
        for cat in data_item['categories']:
            category_dist[cat] = category_dist.get(cat, 0) + 1

        results[brand_name] = {
            'product_count': len(prices),
            'avg_price': round(avg_price),
            'median_price': round(median_price),
            'min_price': round(min_price),
            'max_price': round(max_price),
            'avg_discount_rate': round(avg_discount, 1),
            'price_score': round(hybrid_score, 1),  # -50 ~ +50 스케일
            'sub_normalization_ratio': round(sub_ratio, 1),  # subCategory 정규화 비율
            'category_distribution': category_dist
        }

    # 4. 결과 출력
    print("=" * 60)
    print("브랜드별 하이브리드 가격 점수 (-50 ~ +50)")
    print("=" * 60)

    sorted_brands = sorted(results.items(), key=lambda x: x[1]['price_score'], reverse=True)
    for brand, d in sorted_brands:
        main_cat = max(d['category_distribution'].items(), key=lambda x: x[1])[0] if d['category_distribution'] else 'N/A'
        print(f"[{brand}]")
        print(f"  평균가: {d['avg_price']:,}원 | 주요 카테고리: {main_cat}")
        print(f"  하이브리드 점수: {d['price_score']:+.1f} (sub 정규화 {d['sub_normalization_ratio']:.0f}%)")
        print()

    # 5. 전체 통계
    print("=" * 60)
    print("점수 분포 (-50 ~ +50 스케일)")
    print("=" * 60)
    print(f"점수 범위: {min(all_scores):+.1f} ~ {max(all_scores):+.1f}")
    print(f"점수 평균: {np.mean(all_scores):+.1f}")
    print(f"점수 중앙값: {np.median(all_scores):+.1f}")

    # 6. 결과 저장
    output = {
        "analyzed_at": data.get('crawled_at'),
        "method": "hybrid_category_price_analysis_v3",
        "config": {
            "min_subcategory_count": MIN_SUBCATEGORY_COUNT,
            "score_scale": "-50 to +50"
        },
        "main_category_stats": {
            cat: {
                'min': stats['min'],
                'max': stats['max'],
                'mean': round(stats['mean']),
                'median': round(stats['median']),
                'count': stats['count']
            }
            for cat, stats in main_stats.items()
        },
        "sub_category_stats": {
            cat: {
                'min': stats['min'],
                'max': stats['max'],
                'mean': round(stats['mean']),
                'median': round(stats['median']),
                'count': stats['count']
            }
            for cat, stats in sub_stats.items() if stats['count'] >= MIN_SUBCATEGORY_COUNT
        },
        "overall_stats": {
            "score_min": round(min(all_scores), 1),
            "score_max": round(max(all_scores), 1),
            "score_mean": round(np.mean(all_scores), 1),
            "score_median": round(np.median(all_scores), 1)
        },
        "brands": results
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUTPUT_FILE}")

    # 7. 가격 순위 (하이브리드)
    print("\n## 브랜드 가격 순위 - 하이브리드 정규화 (높은 순)\n")
    for i, (brand, d) in enumerate(sorted_brands, 1):
        print(f"{i:2}. {brand:<15} 점수: {d['price_score']:>+6.1f}  (평균 {d['avg_price']:>8,}원, sub {d['sub_normalization_ratio']:>4.0f}%)")


if __name__ == "__main__":
    main()
