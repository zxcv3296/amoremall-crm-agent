# -*- coding: utf-8 -*-
"""
고객 분석 모듈 - 파생 지표 자동 계산

기존 페르소나 데이터에서 다양한 파생 지표를 계산합니다.
모든 계산은 단순 산술 연산으로 1ms 미만 소요됩니다.
"""

from typing import Dict, Any, List, Tuple


def calculate_customer_value(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    고객 가치 점수 (Customer Lifetime Value 간이 버전)

    계산: 총구매액 기반 + 구매빈도 보정
    """
    purchase = persona.get('purchase', {})

    total_amount = purchase.get('total_amount', 0)
    total_count = purchase.get('total_count', 1)
    avg_amount = purchase.get('avg_amount', 0)
    avg_interval = purchase.get('avg_interval', 30)

    # 연간 예상 구매 횟수
    annual_purchases = 365 / avg_interval if avg_interval > 0 else 12

    # 연간 예상 가치 (CLV 간이)
    annual_value = avg_amount * annual_purchases

    # 등급 산정
    if annual_value >= 2000000:
        tier = "VVIP"
        tier_color = "#9c27b0"
    elif annual_value >= 1000000:
        tier = "VIP"
        tier_color = "#e91e63"
    elif annual_value >= 500000:
        tier = "골드"
        tier_color = "#ff9800"
    elif annual_value >= 200000:
        tier = "실버"
        tier_color = "#9e9e9e"
    else:
        tier = "일반"
        tier_color = "#607d8b"

    return {
        'total_amount': total_amount,
        'avg_amount': avg_amount,
        'annual_value': round(annual_value),
        'annual_purchases': round(annual_purchases, 1),
        'tier': tier,
        'tier_color': tier_color,
        'score': min(100, int(annual_value / 20000))  # 0~100 점수
    }


def calculate_purchase_momentum(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    구매 모멘텀 (상승/하락 추세)

    계산: 구매 주기 비율 기반
    - 주기보다 빨리 구매 → 상승
    - 주기보다 늦게 구매 → 하락
    """
    purchase = persona.get('purchase', {})
    activity = persona.get('activity', {})

    last_purchase_days = purchase.get('last_purchase_days_ago', 30)
    avg_interval = purchase.get('avg_interval', 30)
    last_visit_days = activity.get('last_visit_days_ago', 7)

    # 구매 주기 비율
    cycle_ratio = last_purchase_days / avg_interval if avg_interval > 0 else 1.0

    # 방문 활성도 (최근 방문일 기준)
    if last_visit_days <= 3:
        visit_score = 1.2
    elif last_visit_days <= 7:
        visit_score = 1.0
    elif last_visit_days <= 14:
        visit_score = 0.8
    else:
        visit_score = 0.6

    # 모멘텀 점수 (1.0 = 평균, >1.0 = 상승, <1.0 = 하락)
    momentum = (1 / cycle_ratio) * visit_score if cycle_ratio > 0 else 1.0
    momentum = round(momentum, 2)

    # 추세 판단
    if momentum >= 1.3:
        trend = "급상승"
        trend_icon = "🚀"
        trend_color = "#4CAF50"
    elif momentum >= 1.1:
        trend = "상승"
        trend_icon = "📈"
        trend_color = "#8BC34A"
    elif momentum >= 0.9:
        trend = "유지"
        trend_icon = "➡️"
        trend_color = "#FFC107"
    elif momentum >= 0.7:
        trend = "하락"
        trend_icon = "📉"
        trend_color = "#FF9800"
    else:
        trend = "급하락"
        trend_icon = "⚠️"
        trend_color = "#f44336"

    return {
        'momentum': momentum,
        'cycle_ratio': round(cycle_ratio, 2),
        'visit_score': visit_score,
        'trend': trend,
        'trend_icon': trend_icon,
        'trend_color': trend_color
    }


def calculate_discount_dependency(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    할인 의존도

    계산: (1 - 정가구매비율) × 할인민감도 점수
    """
    promotion = persona.get('promotion', {})

    # 정가 구매 비율 (0~1)
    full_price_ratio = promotion.get('full_price_ratio', 0.5)

    # 할인 민감도 점수화
    sensitivity = promotion.get('discount_sensitivity', '중')
    sensitivity_score = {'높음': 1.0, '중': 0.6, '낮음': 0.3}.get(sensitivity, 0.6)

    # 쿠폰 사용률
    coupon_usage = promotion.get('coupon_usage_rate', 0.5)

    # 할인 의존도 = (1 - 정가비율) × 민감도 × 쿠폰사용률 가중
    dependency = (1 - full_price_ratio) * sensitivity_score * (0.5 + coupon_usage * 0.5)
    dependency = round(dependency, 2)

    # 레벨 판단
    if dependency >= 0.7:
        level = "높음"
        level_color = "#f44336"
        recommendation = "할인 없이는 구매 확률 낮음"
    elif dependency >= 0.4:
        level = "중간"
        level_color = "#FF9800"
        recommendation = "적절한 할인으로 구매 유도"
    else:
        level = "낮음"
        level_color = "#4CAF50"
        recommendation = "프리미엄/신제품 추천 가능"

    return {
        'dependency': dependency,
        'level': level,
        'level_color': level_color,
        'full_price_ratio': full_price_ratio,
        'sensitivity': sensitivity,
        'coupon_usage': coupon_usage,
        'recommendation': recommendation
    }


def calculate_brand_switch_risk(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    브랜드 이탈 위험도

    계산: 브랜드 다양성 × (1 - 충성도)
    """
    brand_info = persona.get('brand', {})

    # 브랜드 다양성 (0~1, 높을수록 다양하게 구매)
    diversity = brand_info.get('diversity', 0.5)

    # 충성도 점수화
    loyalty = brand_info.get('loyalty', '중')
    loyalty_score = {'높음': 0.9, '중': 0.6, '낮음': 0.3}.get(loyalty, 0.6)

    # 이탈 위험 = 다양성 × (1 - 충성도)
    switch_risk = diversity * (1 - loyalty_score)
    switch_risk = round(switch_risk, 2)

    # 주 브랜드 정보
    primary_brand = brand_info.get('primary_brand', 'N/A')
    purchase_counts = brand_info.get('purchase_counts', {})

    # 주 브랜드 점유율
    total_brand_purchases = sum(purchase_counts.values()) if purchase_counts else 1
    primary_share = purchase_counts.get(primary_brand, 0) / total_brand_purchases if total_brand_purchases > 0 else 0

    # 레벨 판단
    if switch_risk >= 0.4:
        level = "높음"
        level_color = "#f44336"
        action = "브랜드 로열티 프로그램 필요"
    elif switch_risk >= 0.2:
        level = "중간"
        level_color = "#FF9800"
        action = "경쟁사 대비 차별화 강조"
    else:
        level = "낮음"
        level_color = "#4CAF50"
        action = "현재 브랜드 충성도 유지"

    return {
        'switch_risk': switch_risk,
        'level': level,
        'level_color': level_color,
        'diversity': diversity,
        'loyalty': loyalty,
        'primary_brand': primary_brand,
        'primary_share': round(primary_share, 2),
        'action': action
    }


def calculate_crosssell_potential(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    크로스셀 가능성

    계산: 카테고리 다양성 × 평균구매액 기반
    """
    purchase = persona.get('purchase', {})

    # 최근 구매 카테고리
    recent_categories = purchase.get('recent_categories', [])
    category_count = len(recent_categories)

    # 평균 구매액
    avg_amount = purchase.get('avg_amount', 30000)

    # 전체 카테고리 목록 (예시)
    all_categories = ['크림', '세럼', '에센스', '스킨', '로션', '클렌징',
                      '마스크', '선케어', '쿠션', '아이케어', '립케어']

    # 미구매 카테고리
    unpurchased = [c for c in all_categories if c not in recent_categories]

    # 크로스셀 점수 (구매력 × 확장 여지)
    expansion_ratio = len(unpurchased) / len(all_categories) if all_categories else 0
    spending_score = min(1.0, avg_amount / 100000)  # 10만원 이상이면 1.0

    potential = expansion_ratio * spending_score
    potential = round(potential, 2)

    # 레벨 판단
    if potential >= 0.5:
        level = "높음"
        level_color = "#4CAF50"
    elif potential >= 0.3:
        level = "중간"
        level_color = "#FF9800"
    else:
        level = "낮음"
        level_color = "#9e9e9e"

    # 추천 카테고리 (미구매 중 상위 3개)
    recommended_categories = unpurchased[:3]

    return {
        'potential': potential,
        'level': level,
        'level_color': level_color,
        'current_categories': recent_categories,
        'category_count': category_count,
        'recommended_categories': recommended_categories,
        'avg_amount': avg_amount
    }


def calculate_promotion_response(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    프로모션 반응 점수

    계산: 쿠폰사용률 × 이벤트참여율
    """
    promotion = persona.get('promotion', {})

    coupon_usage = promotion.get('coupon_usage_rate', 0.5)
    event_participation = promotion.get('event_participation_rate', 0.5)
    preferred_type = promotion.get('preferred_type', '할인')

    # 반응 점수
    response_score = coupon_usage * 0.6 + event_participation * 0.4
    response_score = round(response_score, 2)

    # 레벨 판단
    if response_score >= 0.7:
        level = "매우 적극"
        level_color = "#4CAF50"
        strategy = "모든 프로모션 타겟팅 우선순위"
    elif response_score >= 0.5:
        level = "적극"
        level_color = "#8BC34A"
        strategy = "주요 프로모션 타겟팅"
    elif response_score >= 0.3:
        level = "보통"
        level_color = "#FFC107"
        strategy = "맞춤형 프로모션만 타겟팅"
    else:
        level = "소극"
        level_color = "#9e9e9e"
        strategy = "프로모션보다 정보 제공 중심"

    return {
        'response_score': response_score,
        'level': level,
        'level_color': level_color,
        'coupon_usage': coupon_usage,
        'event_participation': event_participation,
        'preferred_type': preferred_type,
        'strategy': strategy
    }


def calculate_repurchase_timing(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    재구매 타이밍 긴급도

    계산: 경과일 / 평균주기
    """
    purchase = persona.get('purchase', {})

    last_purchase_days = purchase.get('last_purchase_days_ago', 30)
    avg_interval = purchase.get('avg_interval', 30)

    # 주기 비율
    ratio = last_purchase_days / avg_interval if avg_interval > 0 else 1.0

    # 남은 일수 (음수면 초과)
    days_remaining = avg_interval - last_purchase_days

    # 긴급도 판단
    if ratio >= 1.5:
        urgency = "긴급"
        urgency_color = "#f44336"
        urgency_icon = "🔴"
        action = "즉시 재구매 유도 메시지"
    elif ratio >= 1.0:
        urgency = "도래"
        urgency_color = "#FF9800"
        urgency_icon = "🟠"
        action = "재구매 리마인드 메시지"
    elif ratio >= 0.7:
        urgency = "임박"
        urgency_color = "#FFC107"
        urgency_icon = "🟡"
        action = "사전 예고 메시지 고려"
    else:
        urgency = "여유"
        urgency_color = "#4CAF50"
        urgency_icon = "🟢"
        action = "브랜드 관계 유지 메시지"

    return {
        'ratio': round(ratio, 2),
        'days_remaining': days_remaining,
        'last_purchase_days': last_purchase_days,
        'avg_interval': avg_interval,
        'urgency': urgency,
        'urgency_color': urgency_color,
        'urgency_icon': urgency_icon,
        'action': action
    }


def get_full_customer_analysis(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    전체 고객 분석 결과를 한 번에 반환

    Returns:
        모든 파생 지표를 포함한 딕셔너리
    """
    return {
        'customer_value': calculate_customer_value(persona),
        'purchase_momentum': calculate_purchase_momentum(persona),
        'discount_dependency': calculate_discount_dependency(persona),
        'brand_switch_risk': calculate_brand_switch_risk(persona),
        'crosssell_potential': calculate_crosssell_potential(persona),
        'promotion_response': calculate_promotion_response(persona),
        'repurchase_timing': calculate_repurchase_timing(persona)
    }


def get_quick_summary(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    핵심 지표만 빠르게 반환 (UI 헤더용)
    """
    analysis = get_full_customer_analysis(persona)

    return {
        'value_tier': analysis['customer_value']['tier'],
        'value_score': analysis['customer_value']['score'],
        'momentum_trend': analysis['purchase_momentum']['trend'],
        'momentum_icon': analysis['purchase_momentum']['trend_icon'],
        'repurchase_urgency': analysis['repurchase_timing']['urgency'],
        'repurchase_icon': analysis['repurchase_timing']['urgency_icon'],
        'switch_risk': analysis['brand_switch_risk']['level'],
        'promo_response': analysis['promotion_response']['level']
    }


def classify_customer_type(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    고객 성향 유형을 분류합니다.

    유형 (우선순위 순):
    1. 신규 고객: 가입 ≤ 90일, 구매 < 3회
    2. 트렌드 탐색형: 다른 브랜드 비중 ≥ 50%
    3. 실용 효율형: 동일 카테고리 ≥ 70%, 월 구매 ≥ 1회
    4. 가치 지향형: 단일 브랜드 ≥ 80%, 프로모션 < 30%
    5. 성능 신뢰형: 고객단가 높음, 프리미엄 선호
    6. 루틴 유지형: 동일 제품 반복 (충성도 높음, 다양성 낮음)
    7. 일반 고객: 위 조건 미충족

    Returns:
        {
            'type': '트렌드 탐색형',
            'type_code': 'trend_seeker',
            'description': '새로운 브랜드·제품 시도를 즐김',
            'llm_instruction': 'LLM에게 전달할 지시사항',
            'icon': '🔍',
            'color': '#9C27B0'
        }
    """
    purchase = persona.get('purchase', {})
    brand_info = persona.get('brand', {})
    promotion = persona.get('promotion', {})
    activity = persona.get('activity', {})

    # 기본 데이터 추출
    total_count = purchase.get('total_count', 0)
    avg_amount = purchase.get('avg_amount', 30000)
    avg_interval = purchase.get('avg_interval', 30)
    signup_days = persona.get('signup_days_ago', 365)  # 기본값 1년

    diversity = brand_info.get('diversity', 0.5)
    loyalty = brand_info.get('loyalty', '중')
    loyalty_score = {'높음': 0.9, '중': 0.6, '낮음': 0.3}.get(loyalty, 0.6)

    full_price_ratio = promotion.get('full_price_ratio', 0.5)
    discount_sensitivity = promotion.get('discount_sensitivity', '중')

    tier = persona.get('tier', 'mid')

    # ===== 유형 판별 (우선순위 순) =====

    # 1. 신규 고객
    if signup_days <= 90 and total_count < 3:
        return {
            'type': '신규 고객',
            'type_code': 'new_customer',
            'description': '구매 패턴 미형성, 탐색 단계',
            'icon': '🌱',
            'color': '#4CAF50',
            'llm_instruction': """• 개인화 가정 최소화
• 브랜드/아모레몰 이용 맥락 간단 소개
• 베스트셀러·입문용 제품 중심 추천
• '처음', '시작', '부담 없이' 같은 표현 활용"""
        }

    # 2. 트렌드 탐색형: 다양성 높음 (50% 이상)
    if diversity >= 0.5:
        return {
            'type': '트렌드 탐색형',
            'type_code': 'trend_seeker',
            'description': '새로운 브랜드·제품 시도를 즐김',
            'icon': '🔍',
            'color': '#9C27B0',
            'llm_instruction': """• 신제품·트렌드 맥락 강조
• '요즘 주목받는', '최근 선택이 늘어난' 표현 사용
• 선택의 자유를 존중하는 제안형 문장"""
        }

    # 3. 가치 지향형: 단일 브랜드 충성 + 정가 구매
    if loyalty_score >= 0.8 and full_price_ratio >= 0.7:
        return {
            'type': '가치 지향형',
            'type_code': 'value_driven',
            'description': '철학·성분·브랜드 신념 중시',
            'icon': '💎',
            'color': '#3F51B5',
            'llm_instruction': """• 성분·브랜드 철학 설명 중심
• 과장·가격 언급 배제
• '선택의 이유'를 존중하는 차분한 어투"""
        }

    # 4. 성능 신뢰형: 고객단가 높음 + 프리미엄
    if avg_amount >= 80000 or tier == 'premium':
        return {
            'type': '성능 신뢰형',
            'type_code': 'performance_seeker',
            'description': '효능·전문성 중시, 프리미엄 선호',
            'icon': '⭐',
            'color': '#FF5722',
            'llm_instruction': """• 효능·사용 목적·검증 맥락 제시
• 전문가 관점의 신뢰감 유지
• 감성 표현보다 정보 전달 우선"""
        }

    # 5. 실용 효율형: 빠른 구매 주기 + 충성도 중간
    if avg_interval <= 30 and loyalty_score >= 0.5:
        return {
            'type': '실용 효율형',
            'type_code': 'practical_efficient',
            'description': '빠르고 효율적 소비 추구',
            'icon': '⚡',
            'color': '#00BCD4',
            'llm_instruction': """• 기능·효율을 먼저 제시
• 멀티 기능, 세트, 루틴 단축 포인트 강조
• 불필요한 감성 설명 최소화"""
        }

    # 6. 루틴 유지형: 높은 충성도 + 낮은 다양성
    if loyalty_score >= 0.8 and diversity < 0.3:
        return {
            'type': '루틴 유지형',
            'type_code': 'routine_keeper',
            'description': '익숙한 제품 반복 구매',
            'icon': '🔄',
            'color': '#795548',
            'llm_instruction': """• 기존 사용 제품과의 연속성 강조
• '늘 사용하시던', '꾸준히 선택받는' 표현 사용
• 변화 제안 최소화, 리마인드 중심"""
        }

    # 7. 일반 고객 (기본)
    return {
        'type': '일반 고객',
        'type_code': 'general',
        'description': '성향 뚜렷하지 않음',
        'icon': '👤',
        'color': '#607D8B',
        'llm_instruction': """• 특정 성향 단정 금지
• 베스트/큐레이션 중심 중립적 추천
• 부담 없는 선택지 제시"""
    }


def get_shopping_persona(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    쇼핑 성향 페르소나를 분류합니다. (비중 기반 8가지 유형)

    유형:
    - 스마트세이버형 (24%): 가격 우선, 실용적 소비
    - 뷰티인텔리형 (20%): 성분 중시, 피부 문제 예방
    - 프로케어형 (15%): 전문적 관리 투자, 고소득층
    - 홈케어루틴형 (14%): 꾸준한 루틴, DIY 케어
    - 젠더리스형 (13%): 젠더뉴트럴, 더마 제품
    - 쁘띠소비형 (5%): 마이크로 힐링
    - 트렌드스캐너형 (5%): 트렌드 빠른 캐치
    - 스테디단골형 (4%): 검증된 브랜드 신뢰
    """
    purchase = persona.get('purchase', {})
    brand_info = persona.get('brand', {})
    promotion = persona.get('promotion', {})

    avg_amount = purchase.get('avg_amount', 30000)
    total_amount = purchase.get('total_amount', 0)
    diversity = brand_info.get('diversity', 0.5)
    loyalty = brand_info.get('loyalty', '중')
    loyalty_score = {'높음': 0.9, '중': 0.6, '낮음': 0.3}.get(loyalty, 0.6)
    discount_sensitivity = promotion.get('discount_sensitivity', '중')
    full_price_ratio = promotion.get('full_price_ratio', 0.5)
    tier = persona.get('tier', 'mid')

    # 스마트세이버형: 할인 민감 + 정가비율 낮음
    if discount_sensitivity == '높음' and full_price_ratio < 0.4:
        return {
            'type': '스마트세이버형',
            'type_code': 'smart_saver',
            'description': '가격 우선, 실용적 소비, 1+1 선호',
            'weight': '24%',
            'icon': '💰',
            'color': '#FF5722'
        }

    # 프로케어형: 고소득층, 프리미엄
    if tier == 'premium' and avg_amount >= 100000:
        return {
            'type': '프로케어형',
            'type_code': 'pro_care',
            'description': '전문적 관리 투자, 고소득층',
            'weight': '15%',
            'icon': '💎',
            'color': '#9C27B0'
        }

    # 스테디단골형: 충성도 매우 높음 + 다양성 낮음
    if loyalty_score >= 0.9 and diversity < 0.2:
        return {
            'type': '스테디단골형',
            'type_code': 'steady_regular',
            'description': '검증된 브랜드 신뢰',
            'weight': '4%',
            'icon': '🏆',
            'color': '#FFC107'
        }

    # 트렌드스캐너형: 다양성 높음
    if diversity >= 0.7:
        return {
            'type': '트렌드스캐너형',
            'type_code': 'trend_scanner',
            'description': '트렌드 빠른 캐치',
            'weight': '5%',
            'icon': '🔮',
            'color': '#E91E63'
        }

    # 홈케어루틴형: 규칙적 구매
    if loyalty_score >= 0.6 and full_price_ratio >= 0.5:
        return {
            'type': '홈케어루틴형',
            'type_code': 'home_routine',
            'description': '꾸준한 루틴, DIY 케어',
            'weight': '14%',
            'icon': '🏠',
            'color': '#4CAF50'
        }

    # 뷰티인텔리형 (기본)
    return {
        'type': '뷰티인텔리형',
        'type_code': 'beauty_intel',
        'description': '성분 중시, 피부 문제 예방',
        'weight': '20%',
        'icon': '🧪',
        'color': '#2196F3'
    }


def get_message_priority(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    고객에게 적합한 메시지 우선순위를 계산합니다.

    우선순위 체계:
    1. 온보딩 (Onboarding): 신규 고객 환영, 가입 ≤ 90일
    2. 재활성화 (Reactivation): 휴면 위험 고객, 이탈확률 ≥ 35%
    3. 전환유도 (Conversion): 구매 주기 도래, cycle_ratio ≥ 0.8
    4. 참여유도 (Engagement): 활성 고객, 일상적 마케팅

    Returns:
        {
            'priority': 1,
            'priority_name': '온보딩',
            'priority_code': 'onboarding',
            'recommended_purpose': 'new_product',
            'reason': '신규 고객 환영 메시지 우선',
            'color': '#4CAF50'
        }
    """
    # churn_calculator 임포트 (순환 참조 방지)
    from core.churn_calculator import calculate_churn_probability

    purchase = persona.get('purchase', {})
    activity = persona.get('activity', {})

    # 가입일, 구매 횟수
    signup_days = activity.get('signup_days_ago', 365)
    total_count = purchase.get('total_count', 0)
    last_purchase_days = purchase.get('last_purchase_days_ago', 30)
    avg_interval = purchase.get('avg_interval', 30)

    # 구매 주기 비율
    cycle_ratio = last_purchase_days / avg_interval if avg_interval > 0 else 1.0

    # 이탈 확률
    churn_prob, _, _ = calculate_churn_probability(persona)

    # ===== 우선순위 판별 (순서대로) =====

    # 1순위: 온보딩 (신규 고객)
    if signup_days <= 90 and total_count < 5:
        return {
            'priority': 1,
            'priority_name': '온보딩',
            'priority_code': 'onboarding',
            'recommended_purpose': 'new_product',
            'reason': f'신규 가입 {signup_days}일, 첫 구매 유도 필요',
            'color': '#4CAF50',
            'icon': '🌱'
        }

    # 2순위: 재활성화 (휴면 위험)
    if churn_prob >= 0.35:
        if churn_prob >= 0.6:
            purpose = 'churn_prevention'
            reason = f'이탈 위험 {churn_prob:.0%}, 즉시 재활성화 필요'
        else:
            purpose = 'repurchase'
            reason = f'휴면 위험 {churn_prob:.0%}, 재구매 유도 권장'

        return {
            'priority': 2,
            'priority_name': '재활성화',
            'priority_code': 'reactivation',
            'recommended_purpose': purpose,
            'reason': reason,
            'color': '#FF9800',
            'icon': '🔔'
        }

    # 3순위: 전환유도 (구매 주기 도래)
    if cycle_ratio >= 0.8:
        return {
            'priority': 3,
            'priority_name': '전환유도',
            'priority_code': 'conversion',
            'recommended_purpose': 'repurchase',
            'reason': f'구매 주기 {cycle_ratio:.0%} 도래, 재구매 전환 적기',
            'color': '#2196F3',
            'icon': '🛒'
        }

    # 4순위: 참여유도 (활성 고객)
    return {
        'priority': 4,
        'priority_name': '참여유도',
        'priority_code': 'engagement',
        'recommended_purpose': 'best_curation',
        'reason': '활성 고객, 관계 유지 및 크로스셀링 기회',
        'color': '#9C27B0',
        'icon': '💜'
    }


def get_priority_analysis(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    메시지 우선순위와 함께 상세 분석 결과 반환
    """
    priority = get_message_priority(persona)
    cust_type = classify_customer_type(persona)
    shop_persona = get_shopping_persona(persona)

    return {
        'priority': priority,
        'customer_type': cust_type,
        'shopping_persona': shop_persona,
        'summary': f"{priority['priority_name']}({priority['priority']}) → {priority['recommended_purpose']}"
    }


# 테스트용
if __name__ == "__main__":
    # 테스트 페르소나
    test_persona = {
        "name": "테스트",
        "purchase": {
            "total_count": 24,
            "last_purchase_days_ago": 42,
            "avg_interval": 45,
            "total_amount": 3200000,
            "avg_amount": 133333,
            "recent_categories": ["크림", "세럼", "에센스"]
        },
        "activity": {
            "last_visit_days_ago": 7,
            "visit_frequency": "중"
        },
        "brand": {
            "purchase_counts": {"설화수": 18, "헤라": 4, "라네즈": 2},
            "primary_brand": "설화수",
            "loyalty": "높음",
            "diversity": 0.4
        },
        "promotion": {
            "discount_sensitivity": "중",
            "event_participation_rate": 0.65,
            "preferred_type": "사은품",
            "coupon_usage_rate": 0.7,
            "full_price_ratio": 0.6
        }
    }

    print("=" * 60)
    print("Customer Analytics Test")
    print("=" * 60)

    analysis = get_full_customer_analysis(test_persona)

    print(f"\n1. 고객 가치")
    cv = analysis['customer_value']
    print(f"   등급: {cv['tier']} (점수: {cv['score']})")
    print(f"   연간 예상 가치: {cv['annual_value']:,}원")

    print(f"\n2. 구매 모멘텀")
    pm = analysis['purchase_momentum']
    print(f"   추세: {pm['trend_icon']} {pm['trend']} (모멘텀: {pm['momentum']})")

    print(f"\n3. 할인 의존도")
    dd = analysis['discount_dependency']
    print(f"   레벨: {dd['level']} ({dd['dependency']})")
    print(f"   권장: {dd['recommendation']}")

    print(f"\n4. 브랜드 이탈 위험")
    bs = analysis['brand_switch_risk']
    print(f"   레벨: {bs['level']} ({bs['switch_risk']})")
    print(f"   주 브랜드: {bs['primary_brand']} ({bs['primary_share']*100:.0f}%)")

    print(f"\n5. 크로스셀 가능성")
    cp = analysis['crosssell_potential']
    print(f"   레벨: {cp['level']} ({cp['potential']})")
    print(f"   추천 카테고리: {', '.join(cp['recommended_categories'])}")

    print(f"\n6. 프로모션 반응")
    pr = analysis['promotion_response']
    print(f"   레벨: {pr['level']} ({pr['response_score']})")
    print(f"   전략: {pr['strategy']}")

    print(f"\n7. 재구매 타이밍")
    rt = analysis['repurchase_timing']
    print(f"   긴급도: {rt['urgency_icon']} {rt['urgency']}")
    print(f"   경과: {rt['last_purchase_days']}일/{rt['avg_interval']}일 ({rt['ratio']}배)")
    print(f"   액션: {rt['action']}")
