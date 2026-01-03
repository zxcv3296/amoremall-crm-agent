# -*- coding: utf-8 -*-
"""
브랜드별 카테고리 매핑 추출
crawled_products.json에서 브랜드별 취급 카테고리 추출
"""
import json
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def extract_brand_categories():
    with open(os.path.join(BASE_DIR, "crawled_products.json"), "r", encoding="utf-8") as f:
        data = json.load(f)

    products = data.get("products", [])

    # 브랜드별 카테고리 수집
    brand_categories = defaultdict(lambda: defaultdict(int))

    for prod in products:
        brand = prod.get("brandName", "")
        main_cat = prod.get("mainCategory", "")
        sub_cat = prod.get("subCategory", "")

        if brand and main_cat:
            if sub_cat:
                cat_key = f"{main_cat} > {sub_cat}"
            else:
                cat_key = main_cat
            brand_categories[brand][cat_key] += 1

    # 결과 정리 (상품 수 기준 정렬)
    result = {}
    for brand, cats in sorted(brand_categories.items()):
        sorted_cats = sorted(cats.items(), key=lambda x: -x[1])
        result[brand] = {
            "categories": [cat for cat, cnt in sorted_cats],
            "category_counts": {cat: cnt for cat, cnt in sorted_cats}
        }

    # 저장
    output_file = os.path.join(BASE_DIR, "brand_category_mapping.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"브랜드별 카테고리 매핑 저장: {output_file}")
    print(f"총 {len(result)}개 브랜드")

    # 출력
    for brand, info in result.items():
        cats = info["categories"][:5]  # 상위 5개만
        print(f"\n{brand}: {cats}")

    return result

if __name__ == "__main__":
    extract_brand_categories()
