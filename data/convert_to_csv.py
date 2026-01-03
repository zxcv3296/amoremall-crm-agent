# -*- coding: utf-8 -*-
"""
JSON을 CSV로 변환 (UTF-8 BOM 인코딩)
"""
import json
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def convert_products():
    """crawled_products.json -> products.csv"""
    with open(os.path.join(BASE_DIR, "crawled_products.json"), "r", encoding="utf-8") as f:
        data = json.load(f)

    products = data.get("products", [])

    # CSV 필드
    fieldnames = [
        "brandName", "prodName", "onlineProdSn", "onlineProdCode",
        "mainCategory", "subCategory", "detailCategory",
        "price", "salePrice", "discountRate",
        "reviewCount", "avgRating", "imageUrl"
    ]

    output_path = os.path.join(BASE_DIR, "products.csv")
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for prod in products:
            writer.writerow(prod)

    print(f"products.csv 저장 완료: {len(products)}개 상품")
    return len(products)


def convert_reviews():
    """crawled_reviews.json -> reviews.csv"""
    with open(os.path.join(BASE_DIR, "crawled_reviews.json"), "r", encoding="utf-8") as f:
        data = json.load(f)

    # 모든 브랜드의 리뷰를 하나로 합침
    all_reviews = []
    for brand in data.get("brands", []):
        brand_name = brand.get("brandName", "")
        for review in brand.get("reviews", []):
            review["brandName"] = brand_name
            all_reviews.append(review)

    # CSV 필드
    fieldnames = ["brandName", "prodName", "content", "onlineProdSn"]

    output_path = os.path.join(BASE_DIR, "reviews.csv")
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for review in all_reviews:
            writer.writerow(review)

    print(f"reviews.csv 저장 완료: {len(all_reviews)}개 리뷰")
    return len(all_reviews)


if __name__ == "__main__":
    print("=" * 50)
    print("JSON -> CSV 변환")
    print("=" * 50)

    prod_count = convert_products()
    review_count = convert_reviews()

    print("=" * 50)
    print(f"완료! 상품: {prod_count}개, 리뷰: {review_count}개")
    print("=" * 50)
