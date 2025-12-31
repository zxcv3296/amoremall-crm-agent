# -*- coding: utf-8 -*-
"""
상품 데이터 품질 개선 스크립트
- 상품명/설명에서 features 추출
- 상품명/설명에서 target_skin 추출
"""

import sys
sys.path.insert(0, 'c:/Users/MSI/AISystem-2402/AISystem-2402/notion')
from data.personas_full import products
import re

# Features 키워드 매핑
FEATURE_KEYWORDS = {
    "보습": ["보습", "수분", "하이드레이팅", "하이드라", "히알루론", "워터", "모이스처", "촉촉", "hydra", "moisture", "aqua"],
    "미백": ["미백", "브라이트닝", "화이트닝", "톤업", "비타민C", "나이아신아마이드", "잡티", "brightening", "whitening", "tone up"],
    "주름개선": ["주름", "링클", "안티에이징", "탄력", "리프팅", "콜라겐", "레티놀", "펩타이드", "wrinkle", "anti-aging", "firming"],
    "진정": ["진정", "카밍", "수딩", "센서티브", "알로에", "병풀", "시카", "cica", "calming", "soothing", "sensitive"],
    "모공케어": ["모공", "피지", "블랙헤드", "화이트헤드", "각질", "BHA", "AHA", "pore", "sebum"],
    "영양": ["영양", "너리싱", "리치", "크림", "오일", "nourishing", "nutrition", "rich"],
    "클렌징": ["클렌징", "클렌저", "폼", "워시", "세안", "cleansing", "cleanser", "wash", "foam"],
    "선케어": ["선", "자외선", "UV", "SPF", "썬", "sun", "sunscreen", "sunblock"],
    "안티에이징": ["안티에이징", "에이징", "노화", "재생", "리뉴얼", "aging", "renewal", "regeneration"],
    "트러블케어": ["트러블", "여드름", "아크네", "블레미쉬", "trouble", "acne", "blemish"],
    "각질케어": ["각질", "필링", "스크럽", "엑스폴리", "peeling", "scrub", "exfoli"],
    "탄력": ["탄력", "탄탄", "리프팅", "처짐", "elastic", "firm", "lifting"],
    "윤기": ["윤기", "글로우", "광채", "래디언스", "glow", "radiance", "luminous"],
}

# Target Skin 키워드 매핑
SKIN_KEYWORDS = {
    "건성": ["건성", "드라이", "건조", "dry"],
    "지성": ["지성", "오일리", "유분", "oily", "oil control"],
    "복합성": ["복합", "combination", "combo"],
    "민감성": ["민감", "센서티브", "저자극", "순한", "sensitive", "gentle", "mild"],
    "트러블성": ["트러블", "여드름", "아크네", "trouble", "acne"],
    "노화피부": ["노화", "에이징", "주름", "aging", "mature"],
}

# 카테고리별 기본 features
CATEGORY_FEATURES = {
    "클렌저": ["클렌징"],
    "토너": ["보습"],
    "에센스": ["보습", "영양"],
    "세럼": ["보습", "영양"],
    "앰플": ["영양", "안티에이징"],
    "크림": ["보습", "영양"],
    "로션": ["보습"],
    "선케어": ["선케어"],
    "마스크팩": ["보습", "진정"],
    "아이케어": ["주름개선", "영양"],
    "립케어": ["보습", "영양"],
}

def extract_features(product):
    """상품명과 설명에서 features 추출"""
    name = product.get('name', '').lower()
    desc = product.get('description', '').lower()
    category = product.get('category', '')
    text = f"{name} {desc}"

    features = set()

    # 키워드 기반 추출
    for feature, keywords in FEATURE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                features.add(feature)
                break

    # 카테고리 기반 기본 features 추가
    if category in CATEGORY_FEATURES:
        for feat in CATEGORY_FEATURES[category]:
            features.add(feat)

    # 브랜드 특성 기반 추가
    brand = product.get('brand', '')
    if brand == '설화수':
        features.add('영양')
        features.add('안티에이징')
    elif brand == '라네즈':
        features.add('보습')
    elif brand == '이니스프리':
        features.add('진정')
    elif brand == '아이오페':
        features.add('안티에이징')
    elif brand == '프리메라':
        features.add('진정')

    # 최소 1개는 있어야 함
    if not features:
        features.add('기본케어')

    return list(features)


def extract_target_skin(product):
    """상품명과 설명에서 target_skin 추출"""
    name = product.get('name', '').lower()
    desc = product.get('description', '').lower()
    text = f"{name} {desc}"

    skins = set()

    # 키워드 기반 추출
    for skin, keywords in SKIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                skins.add(skin)
                break

    # 브랜드 특성 기반 추가
    brand = product.get('brand', '')
    if brand == '프리메라':
        skins.add('민감성')

    # 아무것도 없으면 모든피부
    if not skins:
        skins.add('모든피부')

    return list(skins)


def enrich_products():
    """상품 데이터 품질 개선"""
    print("=" * 60)
    print("상품 데이터 품질 개선 시작")
    print("=" * 60)

    enriched = []

    # 통계
    feature_changed = 0
    skin_changed = 0

    for p in products:
        # 기존 값 백업
        old_features = p.get('features', ['기본케어'])
        old_skin = p.get('target_skin', p.get('target', ['모든피부']))

        # 새 값 추출
        new_features = extract_features(p)
        new_skin = extract_target_skin(p)

        # 업데이트
        p['features'] = new_features
        p['target_skin'] = new_skin

        # 통계
        if set(old_features) != set(new_features):
            feature_changed += 1
        if set(old_skin) != set(new_skin):
            skin_changed += 1

        enriched.append(p)

    print(f"\nfeatures 변경: {feature_changed}/{len(products)}개")
    print(f"target_skin 변경: {skin_changed}/{len(products)}개")

    return enriched


def save_products(products_list):
    """data_full.py 파일 저장"""

    output = '''# -*- coding: utf-8 -*-
"""
아모레몰 상품 데이터 (1,053개)
자동 생성됨 - 수정하지 마세요
"""

products = [
'''

    for i, p in enumerate(products_list):
        output += "    {\n"
        output += f'        "id": {p.get("id", i+1)},\n'
        output += f'        "name": {repr(p.get("name", ""))},\n'
        output += f'        "brand": {repr(p.get("brand", ""))},\n'
        output += f'        "category": {repr(p.get("category", ""))},\n'
        output += f'        "features": {p.get("features", ["기본케어"])},\n'
        output += f'        "target_skin": {p.get("target_skin", ["모든피부"])},\n'
        output += f'        "price": {p.get("price", 0)},\n'
        output += f'        "discount_rate": {p.get("discount_rate", 0)},\n'
        output += f'        "is_new": {p.get("is_new", False)},\n'
        output += f'        "img_url": {repr(p.get("img_url", ""))},\n'
        output += f'        "description": {repr(p.get("description", ""))},\n'
        output += "    },\n"

    output += "]\n"

    with open('c:/Users/MSI/AISystem-2402/AISystem-2402/notion/data_full.py', 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"\ndata_full.py 저장 완료!")


def show_statistics(products_list):
    """결과 통계 출력"""
    from collections import Counter

    print("\n" + "=" * 60)
    print("개선 후 통계")
    print("=" * 60)

    # features 분포
    print("\n[features 분포]")
    all_features = []
    for p in products_list:
        all_features.extend(p.get('features', []))
    feature_counts = Counter(all_features)
    for feat, count in feature_counts.most_common(15):
        print(f"  {feat}: {count}개")

    # target_skin 분포
    print("\n[target_skin 분포]")
    all_skins = []
    for p in products_list:
        all_skins.extend(p.get('target_skin', []))
    skin_counts = Counter(all_skins)
    for skin, count in skin_counts.most_common():
        print(f"  {skin}: {count}개")

    # 샘플 5개
    print("\n[샘플 상품 5개]")
    import random
    samples = random.sample(products_list, min(5, len(products_list)))
    for p in samples:
        name = p.get('name', '')[:40]
        print(f"\n- {name}")
        print(f"  features: {p.get('features')}")
        print(f"  target_skin: {p.get('target_skin')}")


if __name__ == "__main__":
    # 1. 품질 개선
    enriched = enrich_products()

    # 2. 저장
    save_products(enriched)

    # 3. 통계 출력
    show_statistics(enriched)

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
