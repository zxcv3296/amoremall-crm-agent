# -*- coding: utf-8 -*-
"""
아모레퍼시픽 공식 브랜드 목록 (30개)
- 아모레퍼시픽 공식 브랜드 페이지 기준
- brandSn은 아모레몰에서 추출
- 제외: 구딸(0개), 온호프(1개), 유행화장(1개) - 상품 없거나 극소수
"""

# 아모레퍼시픽 브랜드 (크롤링 대상)
AMORE_BRANDS = [
    # ㄹ
    {"brandSn": 31, "brandName": "라네즈"},
    {"brandSn": 131, "brandName": "라보에이치"},
    {"brandSn": 23, "brandName": "려"},
    {"brandSn": 197, "brandName": "롱테이크"},

    # ㅁ
    {"brandSn": 11, "brandName": "마몽드"},
    {"brandSn": 35, "brandName": "메디안"},
    {"brandSn": 240, "brandName": "메이크온"},
    {"brandSn": 9, "brandName": "미쟝센"},

    # ㅂ
    {"brandSn": 234, "brandName": "바이탈뷰티"},
    {"brandSn": 98, "brandName": "비레디"},

    # ㅅ
    {"brandSn": 18, "brandName": "설화수"},

    # ㅇ
    {"brandSn": 229, "brandName": "아모레베이직"},
    {"brandSn": 121, "brandName": "아모레성수"},
    {"brandSn": 22, "brandName": "아모레퍼시픽"},
    {"brandSn": 17, "brandName": "아이오페"},
    {"brandSn": 203, "brandName": "앞바다즈"},
    {"brandSn": 205, "brandName": "에뛰드"},
    {"brandSn": 206, "brandName": "에스쁘아"},
    {"brandSn": 53, "brandName": "에스트라"},
    {"brandSn": 243, "brandName": "에이피뷰티"},
    {"brandSn": 96, "brandName": "오딧세이"},
    {"brandSn": 207, "brandName": "오설록"},
    {"brandSn": 204, "brandName": "이니스프리"},
    {"brandSn": 19, "brandName": "일리윤"},

    # ㅍ
    {"brandSn": 211, "brandName": "퍼즐우드"},
    {"brandSn": 10, "brandName": "프리메라"},

    # ㅎ
    {"brandSn": 25, "brandName": "한율"},
    {"brandSn": 20, "brandName": "해피바스"},
    {"brandSn": 15, "brandName": "헤라"},
    {"brandSn": 27, "brandName": "홀리추얼"},
]

if __name__ == "__main__":
    print(f"아모레퍼시픽 공식 브랜드: {len(AMORE_BRANDS)}개")
    print("\n브랜드 목록:")
    for i, b in enumerate(AMORE_BRANDS, 1):
        print(f"  {i}. {b['brandName']} (brandSn={b['brandSn']})")
