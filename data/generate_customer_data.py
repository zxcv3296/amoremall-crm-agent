# -*- coding: utf-8 -*-
"""
고객 데이터 생성 스크립트
- 500개: 컬럼별 제약조건 기반 랜덤 생성
- 500개: 페르소나 규칙 기반 생성 (7개 페르소나 균등 분배)
- 총 1000개 + 파생데이터 추가
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

# 30개 브랜드 (삭제된 3개 제외)
BRANDS = [
    "라네즈", "라보에이치", "려", "롱테이크", "마몽드", "메디안", "메이크온",
    "미쟝센", "바이탈뷰티", "비레디", "설화수", "아모레베이직", "아모레성수",
    "아모레퍼시픽", "아이오페", "앞바다즈", "에뛰드", "에스쁘아", "에스트라",
    "에이피뷰티", "오딧세이", "오설록", "이니스프리", "일리윤", "퍼즐우드",
    "프리메라", "한율", "해피바스", "헤라", "홀리추얼"
]

# 페르소나별 브랜드 매핑
PERSONA_BRANDS = {
    "테크니컬 홈케어족": ["메이크온", "바이탈뷰티", "아이오페"],
    "하이엔드 품격가": ["설화수", "헤라", "에이피뷰티"],
    "웰니스 힐링 탐험가": ["퍼즐우드", "오설록", "롱테이크", "바이탈뷰티"],
    "연구소 기반 해결사": ["에스트라", "마몽드", "비레디", "프리메라", "한율", "려", "미쟝센"],
    "트렌디 Z세대": ["앞바다즈", "에스쁘아", "에뛰드", "아모레성수"],
    "합리적 큐레이터": ["라네즈", "한율", "프리메라", "려", "미쟝센", "오딧세이"],
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
CONCERNS_LIST = ["민감성", "트러블", "탄력저하", "주름", "칙칙함", "건조함", "모공", "피지", "홍조", "미백"]

# 프로모션 선호 (비중: 할인>한정>사은품>신상품)
PROMOTIONS = ["할인판매", "한정판매", "사은품증정", "신상품"]
PROMOTION_WEIGHTS = [0.4, 0.25, 0.2, 0.15]

# 멤버십 티어
TIERS = ["A", "M", "O", "R", "E"]

# 방문빈도
VISIT_FREQ = ["높음", "중간", "낮음"]


# ============================================================
# 유틸리티 함수
# ============================================================

def random_date(start_date, end_date):
    """시작일과 종료일 사이의 랜덤 날짜 생성"""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


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


def generate_birthday():
    """생년월일 생성 (2011년 이전, 즉 만 15세 이상)"""
    # 1960년 ~ 2010년
    year = random.randint(1960, 2010)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return datetime(year, month, day)


def calculate_age(birthday):
    """나이 계산 (2026년 기준)"""
    return 2026 - birthday.year


def generate_signup_day(last_visit_day):
    """가입일 생성 (마지막 방문일보다 이전)"""
    # 최소 30일 전 ~ 최대 3년 전
    days_before = random.randint(30, 1095)
    signup = last_visit_day - timedelta(days=days_before)
    return signup


def generate_dates():
    """날짜 데이터 생성 (제약조건 준수)"""
    # last_visit_day: 오늘로부터 1~60일 전
    last_visit_day = TODAY - timedelta(days=random.randint(1, 60))

    # last_purchase_day: last_visit_day와 같거나 이전 (최대 90일 전)
    days_before_visit = random.randint(0, 90)
    last_purchase_day = last_visit_day - timedelta(days=days_before_visit)

    # last_view_day, last_save_day, last_cart_day: last_visit_day와 같거나 이전
    last_view_day = last_visit_day - timedelta(days=random.randint(0, 30))
    last_save_day = last_visit_day - timedelta(days=random.randint(0, 60))
    last_cart_day = last_visit_day - timedelta(days=random.randint(0, 45))

    # last_view_day는 last_save_day, last_cart_day와 같거나 최근이어야 함
    if last_view_day < last_save_day:
        last_view_day = last_save_day
    if last_view_day < last_cart_day:
        last_view_day = last_cart_day

    # signup_day
    signup_day = generate_signup_day(last_visit_day)

    return {
        "signup_day": signup_day,
        "last_purchase_day": last_purchase_day,
        "last_visit_day": last_visit_day,
        "last_view_day": last_view_day,
        "last_save_day": last_save_day,
        "last_cart_day": last_cart_day
    }


def get_membership_tier(signup_days_ago, total_count):
    """멤버십 티어 결정 (가입일수, 구매횟수 고려)"""
    # E: VIP (가입 1년 이상 + 구매 20회 이상)
    # R: 골드 (가입 6개월 이상 + 구매 10회 이상)
    # O: 실버 (가입 3개월 이상 + 구매 5회 이상)
    # M: 일반
    # A: 신규 (가입 30일 이내)

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
    """방문빈도 결정 (구매횟수 고려)"""
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
        # 선호 브랜드 중에서 우선 선택
        selected = random.sample(preferred_brands, min(len(preferred_brands), n))
        # 부족하면 다른 브랜드에서 추가
        if len(selected) < n:
            others = [b for b in BRANDS if b not in selected]
            selected.extend(random.sample(others, min(len(others), n - len(selected))))
        return selected
    else:
        return random.sample(BRANDS, n)


def select_categories(brands, n=None, preferred_categories=None):
    """카테고리 선택 (브랜드별 취급 카테고리 고려, 최대 5개)"""
    # 브랜드별 카테고리 매핑 로드
    mapping_file = os.path.join(BASE_DIR, "brand_category_mapping.json")
    with open(mapping_file, "r", encoding="utf-8") as f:
        brand_categories = json.load(f)

    if n is None:
        n = random.randint(1, 5)

    available_cats = set()
    for brand in brands:
        if brand in brand_categories:
            available_cats.update(brand_categories[brand]["categories"][:5])

    if preferred_categories:
        # 선호 카테고리 우선
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
    """제약조건 기반 랜덤 고객 생성 (500개용)"""
    # 날짜 생성
    dates = generate_dates()
    birthday = generate_birthday()

    # 구매 데이터
    total_count = random.randint(1, 40)  # 최대 40회
    avg_amount = random.randint(15000, 200000)

    # 가입일로부터 경과일수
    signup_days_ago = (TODAY - dates["signup_day"]).days

    # 멤버십, 방문빈도
    membership_tier = get_membership_tier(signup_days_ago, total_count)
    visit_frequency = get_visit_frequency(total_count)

    # 브랜드, 카테고리
    primary_brands = select_brands()
    primary_categories = select_categories(primary_brands)

    # 프로모션 비율
    full_price_ratio = round(random.uniform(0.1, 0.9), 2)
    discount_sensitivity = round(1 - full_price_ratio, 2)
    coupon_usage_rate = round(random.uniform(0.1, 0.9), 2)
    event_participation_rate = round(random.uniform(0.1, 0.95), 2)

    # 프로모션 선호
    preferred_promotion = random.choices(PROMOTIONS, weights=PROMOTION_WEIGHTS)[0]

    # 다양성, 세션시간
    diversity = round(random.uniform(0.1, 0.99), 2)
    avg_session_minutes = random.randint(3, 40)

    return {
        "brand_cluster": "",  # 나중에 라벨링
        "persona": "",  # 나중에 라벨링
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
        "full_price_ratio": full_price_ratio,
        "discount_sensitivity": discount_sensitivity,
        "coupon_usage_rate": coupon_usage_rate,
        "event_participation_rate": event_participation_rate,
        "preferred_promotion": preferred_promotion,
        "diversity": diversity,
        "avg_session_minutes": avg_session_minutes
    }


def generate_persona_customer(customer_id, persona):
    """페르소나 규칙 기반 고객 생성 (500개용 - 균등 분배)"""
    # 기본 데이터는 랜덤 생성과 동일
    customer = generate_random_customer(customer_id)

    # 페르소나별 특성 적용
    preferred_brands = PERSONA_BRANDS.get(persona, BRANDS)
    preferred_categories = PERSONA_CATEGORIES.get(persona, [])

    # 브랜드 재설정 (페르소나 브랜드 우선)
    primary_brands = select_brands(preferred_brands=preferred_brands)
    primary_categories = select_categories(primary_brands, preferred_categories=preferred_categories)

    customer["primary_brand"] = ",".join(primary_brands)
    customer["primary_category"] = ", ".join(primary_categories)

    # 페르소나별 특성 조정
    if persona == "테크니컬 홈케어족":
        customer["avg_amount"] = random.randint(80000, 200000)  # 상위 10%
        customer["full_price_ratio"] = round(random.uniform(0.5, 0.9), 2)

    elif persona == "하이엔드 품격가":
        customer["avg_amount"] = random.randint(100000, 250000)  # 100,000원 이상
        customer["preferred_promotion"] = random.choice(["신상품", "한정판매"])
        customer["full_price_ratio"] = round(random.uniform(0.6, 0.95), 2)

    elif persona == "웰니스 힐링 탐험가":
        customer["avg_amount"] = random.randint(30000, 100000)  # 1분위수 이상

    elif persona == "연구소 기반 해결사":
        # skin_type, concerns 반드시 있어야 함
        customer["skin_type"] = random.choice(SKIN_TYPES)
        customer["concerns"] = generate_concerns()
        while customer["concerns"] == "고민없음":
            customer["concerns"] = generate_concerns()

    elif persona == "트렌디 Z세대":
        # 25세 미만
        birthday = generate_birthday()
        while calculate_age(birthday) >= 25:
            birthday = generate_birthday()
        customer["birthday"] = format_date(birthday)
        customer["preferred_promotion"] = random.choice(["신상품", "사은품증정"])

    elif persona == "합리적 큐레이터":
        customer["visit_frequency"] = random.choice(["높음", "중간"])
        customer["diversity"] = round(random.uniform(0.5, 0.99), 2)
        customer["avg_session_minutes"] = random.randint(15, 40)  # 3분위수 이상

    elif persona == "실속형 가계 수호자":
        customer["avg_amount"] = random.randint(15000, 50000)  # 50,000원 이하
        customer["preferred_promotion"] = "할인판매"

    # 페르소나 라벨 설정
    cluster_map = {
        "테크니컬 홈케어족": "프리미엄 기능",
        "하이엔드 품격가": "프리미엄 밸런스",
        "웰니스 힐링 탐험가": "중가 라이프스타일",
        "연구소 기반 해결사": "중가 필수케어",
        "트렌디 Z세대": "대중 감성",
        "합리적 큐레이터": "대중 밸런스",
        "실속형 가계 수호자": "대중 필수케어"
    }

    customer["persona"] = persona
    customer["brand_cluster"] = cluster_map.get(persona, "")

    return customer


def add_derived_columns(customer):
    """파생 데이터 추가"""
    # age 계산
    birthday = datetime.strptime(customer["birthday"], "%Y.%m.%d")
    customer["age"] = calculate_age(birthday)

    # total_amount 계산
    customer["total_amount"] = customer["total_count"] * customer["avg_amount"]

    # avg_interval (평균 구매 주기) 계산
    last_purchase = datetime.strptime(customer["last_purchase_day"], "%Y.%m.%d")
    signup = datetime.strptime(customer["signup_day"], "%Y.%m.%d")
    days_since_signup = (last_purchase - signup).days
    if customer["total_count"] > 1:
        customer["avg_interval"] = round(days_since_signup / (customer["total_count"] - 1), 1)
    else:
        customer["avg_interval"] = days_since_signup

    return customer


def generate_all_customers():
    """전체 1000개 고객 데이터 생성"""
    customers = []

    # 1. 랜덤 500개
    print("랜덤 고객 데이터 500개 생성 중...")
    for i in range(1, 501):
        customer = generate_random_customer(generate_customer_id(i))
        customers.append(customer)

    # 2. 페르소나 기반 500개 (7개 페르소나 균등 분배: 각 ~71개)
    print("페르소나 기반 고객 데이터 500개 생성 중...")
    personas = list(PERSONA_BRANDS.keys())
    per_persona = 500 // len(personas)  # 71개
    remainder = 500 % len(personas)  # 3개

    idx = 501
    for i, persona in enumerate(personas):
        count = per_persona + (1 if i < remainder else 0)
        for _ in range(count):
            customer = generate_persona_customer(generate_customer_id(idx), persona)
            customers.append(customer)
            idx += 1

    # 3. 파생 데이터 추가
    print("파생 데이터 추가 중...")
    for customer in customers:
        add_derived_columns(customer)

    return customers


def save_to_csv(customers, filename):
    """CSV로 저장 (UTF-8 BOM)"""
    import csv

    output_path = os.path.join(BASE_DIR, filename)

    # 컬럼 순서
    columns = [
        "brand_cluster", "persona", "customer_id", "name", "birthday", "age",
        "signup_day", "last_purchase_day", "last_visit_day", "last_view_day",
        "last_save_day", "last_cart_day", "skin_type", "concerns", "membership_tier",
        "total_count", "avg_amount", "total_amount", "avg_interval", "visit_frequency",
        "primary_brand", "primary_category", "full_price_ratio", "discount_sensitivity",
        "coupon_usage_rate", "event_participation_rate", "preferred_promotion",
        "diversity", "avg_session_minutes"
    ]

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

    # 데이터 생성
    customers = generate_all_customers()

    print(f"\n총 {len(customers)}개 고객 데이터 생성 완료")

    # 페르소나 분포 확인
    persona_counts = defaultdict(int)
    for c in customers:
        if c["persona"]:
            persona_counts[c["persona"]] += 1
        else:
            persona_counts["미라벨링"] += 1

    print("\n페르소나 분포:")
    for persona, count in sorted(persona_counts.items()):
        print(f"  {persona}: {count}개")

    # CSV 저장
    save_to_csv(customers, "customer_data_1000.csv")

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
