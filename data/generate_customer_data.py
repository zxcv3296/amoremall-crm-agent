# -*- coding: utf-8 -*-
"""
고객 데이터 생성 스크립트
========================
[1] 500개: 컬럼별 제약조건 기반 랜덤 생성 (라벨 없음)
[2] 500개: 페르소나 필터링 규칙 기반 생성 (라벨 없음, 테스트용)
[3] 파생데이터는 마지막에 추가
[4] 별도 CSV로 분리 저장
"""
import json
import random
import os
from datetime import datetime, timedelta
from collections import defaultdict

# 기준 날짜
TODAY = datetime(2026, 1, 3)

# 데이터 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 상수 정의
# ============================================================

# 30개 브랜드
BRANDS = [
    "라네즈", "라보에이치", "려", "롱테이크", "마몽드", "메디안", "메이크온",
    "미쟝센", "바이탈뷰티", "비레디", "설화수", "아모레베이직", "아모레성수",
    "아모레퍼시픽", "아이오페", "앞바다즈", "에뛰드", "에스쁘아", "에스트라",
    "에이피뷰티", "오딧세이", "오설록", "이니스프리", "일리윤", "퍼즐우드",
    "프리메라", "한율", "해피바스", "헤라", "홀리추얼"
]

# 페르소나별 브랜드 매핑 (BRAND_CLUSTERS와 일치)
PERSONA_BRANDS = {
    "테크니컬 홈케어족": ["메이크온", "아이오페", "바이탈뷰티"],
    "하이엔드 품격가": ["설화수", "헤라", "에이피뷰티", "라네즈", "아모레퍼시픽"],
    "웰니스 힐링 탐험가": ["퍼즐우드", "오설록", "롱테이크"],
    "연구소 기반 해결사": ["프리메라", "한율", "에스트라", "비레디", "려", "미쟝센", "마몽드"],
    "트렌디 Z세대": ["앞바다즈", "에스쁘아", "에뛰드", "아모레성수"],
    "합리적 큐레이터": ["오딧세이", "이니스프리", "홀리추얼"],
    "실속형 가계 수호자": ["일리윤", "라보에이치", "해피바스", "아모레베이직", "메디안"]
}

# 페르소나별 카테고리
PERSONA_CATEGORIES = {
    "테크니컬 홈케어족": [
        "뷰티 디바이스 > 페이셜 케어 기기", "뷰티 디바이스 > 구강케어 기기",
        "스킨케어 > 클렌징", "스킨케어 > 모이스처라이징", "스킨케어 > 스페셜 케어"
    ],
    "하이엔드 품격가": [
        "스킨케어 > 모이스처라이징", "메이크업 > 페이스", "스킨케어 > 스페셜 케어",
        "선물추천", "스킨케어 > 세트"
    ],
    "웰니스 힐링 탐험가": [
        "뷰티푸드 > 건강식품", "뷰티푸드 > 차(TEA) / 간식",
        "소품 & 도구 > 캔들 & 디퓨저", "향수 > 향수"
    ],
    "연구소 기반 해결사": [
        "스킨케어 > 클렌징", "스킨케어 > 모이스처라이징", "스킨케어 > 스페셜 케어",
        "스킨케어 > 선케어", "생활용품 > 헤어"
    ],
    "트렌디 Z세대": [
        "메이크업 > 아이", "메이크업 > 립", "메이크업 > 페이스",
        "향수 > 향수", "소품 & 도구"
    ],
    "합리적 큐레이터": [
        "스킨케어 > 모이스처라이징", "스킨케어 > 클렌징", "생활용품 > 헤어",
        "메이크업 > 페이스", "스킨케어 > 세트"
    ],
    "실속형 가계 수호자": [
        "생활용품 > 바디", "생활용품 > 구강", "생활용품 > 헤어",
        "스킨케어 > 선케어", "베이비 > 스킨/바디케어"
    ]
}

# 피부타입
SKIN_TYPES = ["복합성", "건성", "극건성", "지성", "수분부족지성", "중성"]

# 피부고민
CONCERNS_LIST = ["민감성", "트러블", "탄력저하", "주름", "칙칙함", "건조함", "모공"]

# 프로모션 선호 (비중: 할인>한정>사은품>신상품)
PROMOTIONS = ["할인판매", "한정판매", "사은품증정", "신상품"]
PROMOTION_WEIGHTS = [0.4, 0.25, 0.2, 0.15]

# 멤버십 티어
TIERS = ["A", "M", "O", "R", "E"]

# 방문빈도
VISIT_FREQ = ["높음", "중간", "낮음"]


# ============================================================
# 브랜드별 카테고리 매핑 로드
# ============================================================
def load_brand_categories():
    mapping_file = os.path.join(BASE_DIR, "brand_category_mapping.json")
    with open(mapping_file, "r", encoding="utf-8") as f:
        return json.load(f)

BRAND_CATEGORIES = None  # 전역 변수로 로드


# ============================================================
# 유틸리티 함수
# ============================================================

def format_date(dt):
    """날짜 포맷"""
    return dt.strftime("%Y.%m.%d")


def generate_customer_id(index):
    """고객 ID 생성"""
    return f"C{index:04d}"


def generate_name():
    """랜덤 이름 생성"""
    last_names = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍"]
    first_names = ["서연", "민준", "서윤", "예준", "지우", "도윤", "서현", "시우", "하은", "주원",
                   "하윤", "지호", "수아", "준서", "지아", "현우", "은서", "유준", "다은", "건우",
                   "소희", "민서", "지원", "수빈", "예진", "현서", "다윤", "시현", "채원", "유진"]
    return random.choice(last_names) + random.choice(first_names)


def generate_birthday(min_age=14, max_age=65):
    """생년월일 생성 (2011년 이전 = 만 14세 이상)"""
    year = random.randint(2026 - max_age, 2011)  # 1961 ~ 2011
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return datetime(year, month, day)


def calculate_age(birthday):
    """만 나이 계산 (2026년 1월 3일 기준)"""
    age = TODAY.year - birthday.year
    if (TODAY.month, TODAY.day) < (birthday.month, birthday.day):
        age -= 1
    return age


def generate_dates():
    """날짜 데이터 생성 (제약조건 준수)"""
    last_visit_day = TODAY - timedelta(days=random.randint(1, 60))
    days_before_visit = random.randint(0, 90)
    last_purchase_day = last_visit_day - timedelta(days=days_before_visit)
    last_view_day = last_visit_day - timedelta(days=random.randint(0, 30))
    last_save_day = last_visit_day - timedelta(days=random.randint(0, 60))
    last_cart_day = last_visit_day - timedelta(days=random.randint(0, 45))
    days_before = random.randint(30, 1095)
    signup_day = last_visit_day - timedelta(days=days_before)

    return {
        "signup_day": signup_day,
        "last_purchase_day": last_purchase_day,
        "last_visit_day": last_visit_day,
        "last_view_day": last_view_day,
        "last_save_day": last_save_day,
        "last_cart_day": last_cart_day
    }


def get_membership_tier(signup_days_ago, total_count):
    """멤버십 티어 결정"""
    if signup_days_ago <= 30:
        return "A"
    elif signup_days_ago >= 365 and total_count >= 20:
        return "E"
    elif signup_days_ago >= 180 and total_count >= 10:
        return "R"
    elif signup_days_ago >= 90 and total_count >= 5:
        return "O"
    else:
        return "M"


def get_visit_frequency(total_count):
    """방문빈도 결정"""
    if total_count >= 20:
        return random.choices(["높음", "중간", "낮음"], weights=[0.7, 0.25, 0.05])[0]
    elif total_count >= 10:
        return random.choices(["높음", "중간", "낮음"], weights=[0.3, 0.5, 0.2])[0]
    else:
        return random.choices(["높음", "중간", "낮음"], weights=[0.1, 0.3, 0.6])[0]


def select_brands(n=None, preferred_brands=None):
    """브랜드 선택 (최대 5개)"""
    if n is None:
        n = random.randint(1, 5)

    if preferred_brands:
        selected = random.sample(preferred_brands, min(len(preferred_brands), n))
        if len(selected) < n:
            others = [b for b in BRANDS if b not in selected]
            selected.extend(random.sample(others, min(len(others), n - len(selected))))
        return selected
    else:
        return random.sample(BRANDS, n)


def select_categories(brands, n=None, preferred_categories=None):
    """카테고리 선택 (브랜드별 취급 카테고리 고려)"""
    global BRAND_CATEGORIES
    if BRAND_CATEGORIES is None:
        BRAND_CATEGORIES = load_brand_categories()

    if n is None:
        n = random.randint(1, 5)

    available_cats = set()
    for brand in brands:
        if brand in BRAND_CATEGORIES:
            available_cats.update(BRAND_CATEGORIES[brand]["categories"][:5])

    if preferred_categories:
        matching = [c for c in preferred_categories if c in available_cats]
        if matching:
            selected = random.sample(matching, min(len(matching), n))
        else:
            selected = []

        if len(selected) < n and available_cats:
            remaining = list(available_cats - set(selected))
            selected.extend(random.sample(remaining, min(len(remaining), n - len(selected))))
        return selected
    else:
        if available_cats:
            return random.sample(list(available_cats), min(len(available_cats), n))
        return []


def generate_concerns():
    """피부고민 생성 (1~3개 또는 고민없음)"""
    if random.random() < 0.1:
        return "고민없음"
    n = random.randint(1, 3)
    return ",".join(random.sample(CONCERNS_LIST, n))


# ============================================================
# 고객 데이터 생성 함수
# ============================================================

def generate_random_customer(customer_id):
    """[1] 컬럼별 제약조건 기반 랜덤 고객 생성 (라벨 없음)"""
    dates = generate_dates()
    birthday = generate_birthday()
    total_count = random.randint(1, 40)
    avg_amount = random.randint(15000, 200000)
    signup_days_ago = (TODAY - dates["signup_day"]).days
    membership_tier = get_membership_tier(signup_days_ago, total_count)
    visit_frequency = get_visit_frequency(total_count)
    primary_brands = select_brands()
    primary_categories = select_categories(primary_brands)
    coupon_usage_rate = round(random.uniform(0.1, 0.5), 2)
    event_participation_rate = round(random.uniform(0.1, min(0.5, 1 - coupon_usage_rate)), 2)
    preferred_promotion = random.choices(PROMOTIONS, weights=PROMOTION_WEIGHTS)[0]
    avg_session_minutes = random.randint(3, 40)

    return {
        "customer_id": customer_id,
        "name": generate_name(),
        "birthday": format_date(birthday),
        "signup_day": format_date(dates["signup_day"]),
        "last_purchase_day": format_date(dates["last_purchase_day"]),
        "last_visit_day": format_date(dates["last_visit_day"]),
        "last_view_day": format_date(dates["last_view_day"]),
        "last_save_day": format_date(dates["last_save_day"]),
        "last_cart_day": format_date(dates["last_cart_day"]),
        "skin_type": random.choice(SKIN_TYPES),
        "concerns": generate_concerns(),
        "membership_tier": membership_tier,
        "total_count": total_count,
        "avg_amount": avg_amount,
        "visit_frequency": visit_frequency,
        "primary_brand": ",".join(primary_brands),
        "primary_category": ", ".join(primary_categories),
        "coupon_usage_rate": coupon_usage_rate,
        "event_participation_rate": event_participation_rate,
        "preferred_promotion": preferred_promotion,
        "avg_session_minutes": avg_session_minutes
    }


def generate_persona_customer_unlabeled(customer_id, persona):
    """[2] 페르소나 필터링 규칙 기반 생성 (라벨 없음 - 테스트용)

    페르소나 분류 규칙에 맞는 데이터를 생성하되, 라벨은 포함하지 않음
    나중에 수기 라벨링하거나 분류기로 테스트할 용도
    """
    customer = generate_random_customer(customer_id)

    preferred_brands = PERSONA_BRANDS.get(persona, BRANDS)
    preferred_categories = PERSONA_CATEGORIES.get(persona, [])

    # 브랜드 재설정 (페르소나 브랜드 우선 - 최소 2개 이상)
    n_persona_brands = min(len(preferred_brands), random.randint(2, 4))
    primary_brands = random.sample(preferred_brands, n_persona_brands)

    # 추가 브랜드 (0~2개)
    if random.random() < 0.3:
        others = [b for b in BRANDS if b not in primary_brands]
        extra = random.sample(others, min(len(others), random.randint(0, 2)))
        primary_brands.extend(extra)

    primary_categories = select_categories(primary_brands, preferred_categories=preferred_categories)

    customer["primary_brand"] = ",".join(primary_brands)
    customer["primary_category"] = ", ".join(primary_categories)

    # 페르소나별 특성 조정 (분류 규칙에 맞게)
    if persona == "테크니컬 홈케어족":
        # 메이크온 포함 AND (avg_amount > 100000 OR 아이오페/바이탈뷰티)
        customer["avg_amount"] = random.randint(80000, 200000)

    elif persona == "하이엔드 품격가":
        # 설화수/헤라 포함 AND full_price_ratio > 0.6 AND tier in [R, E]
        customer["avg_amount"] = random.randint(100000, 250000)
        customer["coupon_usage_rate"] = round(random.uniform(0.05, 0.2), 2)
        customer["event_participation_rate"] = round(random.uniform(0.05, 0.15), 2)
        customer["membership_tier"] = random.choice(["R", "E"])
        customer["preferred_promotion"] = random.choice(["신상품", "한정판매"])

    elif persona == "웰니스 힐링 탐험가":
        # 오설록/퍼즐우드/롱테이크 중 2개 이상 OR (1개 AND diversity > 0.5)
        customer["avg_amount"] = random.randint(30000, 100000)

    elif persona == "연구소 기반 해결사":
        # 프리메라/에스트라/한율/비레디 포함 AND 민감성/진정 관련
        customer["skin_type"] = random.choice(["민감성", "복합성", "건성"])
        concerns = ["민감성"]
        if random.random() < 0.5:
            concerns.append(random.choice(["건조함", "트러블", "진정"]))
        customer["concerns"] = ",".join(concerns)

    elif persona == "트렌디 Z세대":
        # 나이 < 25 AND 트렌디 브랜드 매칭
        birthday = generate_birthday(min_age=14, max_age=24)
        customer["birthday"] = format_date(birthday)
        customer["preferred_promotion"] = random.choice(["신상품", "사은품증정"])

    elif persona == "합리적 큐레이터":
        # 이니스프리/홀리추얼/오딧세이 포함
        customer["visit_frequency"] = random.choice(["높음", "중간"])
        customer["avg_session_minutes"] = random.randint(15, 40)
        customer["coupon_usage_rate"] = round(random.uniform(0.2, 0.4), 2)
        customer["event_participation_rate"] = round(random.uniform(0.1, 0.25), 2)

    elif persona == "실속형 가계 수호자":
        # 일리윤/라보에이치/해피바스/메디안 포함 AND coupon_usage_rate > 0.5
        customer["avg_amount"] = random.randint(15000, 50000)
        customer["coupon_usage_rate"] = round(random.uniform(0.5, 0.7), 2)
        customer["event_participation_rate"] = round(random.uniform(0.1, 0.3), 2)
        customer["preferred_promotion"] = "할인판매"

    # 라벨은 포함하지 않음 (테스트/수기라벨링용)
    return customer


def add_derived_columns(customer):
    """[3] 파생 데이터 추가"""
    birthday = datetime.strptime(customer["birthday"], "%Y.%m.%d")
    signup_day = datetime.strptime(customer["signup_day"], "%Y.%m.%d")
    last_visit_day = datetime.strptime(customer["last_visit_day"], "%Y.%m.%d")
    last_view_day = datetime.strptime(customer["last_view_day"], "%Y.%m.%d")
    last_save_day = datetime.strptime(customer["last_save_day"], "%Y.%m.%d")
    last_cart_day = datetime.strptime(customer["last_cart_day"], "%Y.%m.%d")
    last_purchase_day = datetime.strptime(customer["last_purchase_day"], "%Y.%m.%d")

    # age
    customer["age"] = calculate_age(birthday)

    # total_amount
    customer["total_amount"] = customer["total_count"] * customer["avg_amount"]

    # average_transaction_value
    customer["average_transaction_value"] = customer["avg_amount"]

    # diversity
    brand_count = len(customer["primary_brand"].split(",")) if customer["primary_brand"] else 1
    category_count = len(customer["primary_category"].split(", ")) if customer["primary_category"] else 1
    diversity = (2 - ((1 / brand_count) + (1 / category_count))) / 2
    customer["diversity"] = round(max(0, min(1, diversity)), 2)

    # full_price_ratio
    full_price_ratio = 1 - (customer["coupon_usage_rate"] + customer["event_participation_rate"])
    customer["full_price_ratio"] = round(max(0, full_price_ratio), 2)

    # discount_sensitivity
    customer["discount_sensitivity"] = round(1 - customer["full_price_ratio"], 2)

    # days_ago 파생변수
    customer["signup_days_ago"] = (TODAY - signup_day).days
    customer["visit_days_ago"] = (TODAY - last_visit_day).days
    customer["view_days_ago"] = (TODAY - last_view_day).days
    customer["save_days_ago"] = (TODAY - last_save_day).days
    customer["cart_days_ago"] = (TODAY - last_cart_day).days
    customer["purchase_days_ago"] = (TODAY - last_purchase_day).days

    return customer


def save_to_csv(customers, filename, include_label_columns=False):
    """CSV로 저장 (UTF-8 BOM)"""
    import csv

    output_path = os.path.join(BASE_DIR, filename)

    # 컬럼 순서
    columns = [
        "customer_id", "name", "birthday", "age",
        "signup_day", "last_purchase_day", "last_visit_day", "last_view_day",
        "last_save_day", "last_cart_day",
        "skin_type", "concerns", "membership_tier",
        "total_count", "avg_amount", "total_amount", "average_transaction_value",
        "visit_frequency", "primary_brand", "primary_category",
        "full_price_ratio", "discount_sensitivity", "coupon_usage_rate",
        "event_participation_rate", "preferred_promotion",
        "diversity", "avg_session_minutes",
        "signup_days_ago", "visit_days_ago", "view_days_ago",
        "save_days_ago", "cart_days_ago", "purchase_days_ago"
    ]

    # 라벨 컬럼 추가 옵션
    if include_label_columns:
        columns = ["brand_cluster", "persona"] + columns

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(customers)

    print(f"저장 완료: {output_path}")
    return output_path


def main():
    print("=" * 60)
    print("고객 데이터 생성 시작")
    print(f"기준 날짜: {format_date(TODAY)}")
    print("=" * 60)

    # ==========================================
    # [1] 랜덤 500개 생성 (라벨 없음)
    # ==========================================
    print("\n[1] 컬럼 제약조건 기반 랜덤 고객 500개 생성 중...")
    random_customers = []
    for i in range(1, 501):
        customer = generate_random_customer(generate_customer_id(i))
        random_customers.append(customer)

    # 파생데이터 추가
    for customer in random_customers:
        add_derived_columns(customer)

    print(f"    생성 완료: {len(random_customers)}개")

    # ==========================================
    # [2] 페르소나 기반 500개 생성 (라벨 없음, 테스트용)
    # ==========================================
    print("\n[2] 페르소나 필터링 규칙 기반 테스트 데이터 500개 생성 중...")
    test_customers = []
    personas = list(PERSONA_BRANDS.keys())
    per_persona = 500 // len(personas)  # 71개
    remainder = 500 % len(personas)  # 3개

    idx = 501
    persona_counts = defaultdict(int)
    for i, persona in enumerate(personas):
        count = per_persona + (1 if i < remainder else 0)
        persona_counts[persona] = count
        for _ in range(count):
            customer = generate_persona_customer_unlabeled(generate_customer_id(idx), persona)
            test_customers.append(customer)
            idx += 1

    # 파생데이터 추가
    for customer in test_customers:
        add_derived_columns(customer)

    print(f"    생성 완료: {len(test_customers)}개")
    print("    페르소나별 분포 (생성 기준, 라벨 미포함):")
    for persona, count in persona_counts.items():
        print(f"      {persona}: {count}개")

    # ==========================================
    # [3] CSV 분리 저장
    # ==========================================
    print("\n[3] CSV 파일 저장 중...")

    # 랜덤 500개
    save_to_csv(random_customers, "customer_data_500_random.csv", include_label_columns=True)

    # 테스트 500개
    save_to_csv(test_customers, "customer_data_500_test.csv", include_label_columns=True)

    # 전체 1000개 (통합)
    all_customers = random_customers + test_customers
    save_to_csv(all_customers, "customer_data_1000.csv", include_label_columns=True)

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
    print("\n생성된 파일:")
    print("  - customer_data_500_random.csv  : 랜덤 생성 (수기 라벨링용)")
    print("  - customer_data_500_test.csv    : 페르소나 규칙 기반 (테스트용)")
    print("  - customer_data_1000.csv        : 전체 통합")


if __name__ == "__main__":
    main()
