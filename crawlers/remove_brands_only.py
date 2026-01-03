# -*- coding: utf-8 -*-
"""
3개 브랜드 제거 스크립트
"""
import json
import os
import sys

# stdout을 utf-8로 설정
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "crawled_products.json")
REVIEWS_FILE = os.path.join(DATA_DIR, "crawled_reviews.json")

BRANDS_TO_REMOVE = ["정글몬스터", "아모스 프로페셔널", "라 리베라"]

print("=" * 60)
print("3개 브랜드 제거 시작")
print(f"제거 대상: {BRANDS_TO_REMOVE}")
print("=" * 60)

# Products 파일 처리
with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
    products_data = json.load(f)

original_prod_count = len(products_data["products"])
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

removed_products = original_prod_count - len(products_data["products"])
print(f"Products: {original_prod_count} -> {len(products_data['products'])} (제거: {removed_products})")

with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
    json.dump(products_data, f, ensure_ascii=False, indent=2)

# Reviews 파일 처리
with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
    reviews_data = json.load(f)

original_brand_count = len(reviews_data["brands"])
reviews_data["brands"] = [
    b for b in reviews_data["brands"]
    if b.get("brandName") not in BRANDS_TO_REMOVE
]

removed_brands = original_brand_count - len(reviews_data["brands"])
print(f"Reviews: {original_brand_count} -> {len(reviews_data['brands'])} 브랜드 (제거: {removed_brands})")

with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
    json.dump(reviews_data, f, ensure_ascii=False, indent=2)

print("=" * 60)
print("브랜드 제거 완료!")
print("=" * 60)
