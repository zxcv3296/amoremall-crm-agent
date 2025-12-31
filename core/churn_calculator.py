# -*- coding: utf-8 -*-
"""
이탈 확률 자동 계산 모듈

구매 패턴 기반으로 고객 이탈 확률을 계산합니다.
하드코딩된 값 대신 실제 데이터 기반 계산을 수행합니다.
"""

from typing import Dict, Any, Tuple, List


def calculate_churn_probability(persona: Dict[str, Any]) -> Tuple[float, str, List[str]]:
    """
    페르소나의 구매 패턴을 기반으로 이탈 확률을 계산합니다.

    계산 공식:
    - 기본: (마지막구매경과일 / 평균구매주기) 기반 점수
    - 보정: 방문 빈도, 프로모션 민감도, 브랜드 충성도 반영

    Args:
        persona: 페르소나 데이터 딕셔너리

    Returns:
        (이탈확률, 위험레벨, 위험요인리스트) 튜플
    """
    purchase = persona.get('purchase', {})
    activity = persona.get('activity', {})
    promotion = persona.get('promotion', {})
    brand = persona.get('brand', {})

    # 기본 데이터 추출
    last_purchase_days = purchase.get('last_purchase_days_ago', 30)
    avg_interval = purchase.get('avg_interval', 30)
    total_purchases = purchase.get('total_count', 0)

    # ========== 1. 구매 주기 기반 기본 점수 (0~1) ==========
    # 마지막 구매 경과일 / 평균 구매 주기 비율
    if avg_interval > 0:
        cycle_ratio = last_purchase_days / avg_interval
    else:
        cycle_ratio = 1.0

    # 비율에 따른 기본 이탈 확률
    if cycle_ratio >= 2.5:
        base_score = 0.9  # 평균의 2.5배 이상 경과 → 매우 높음
    elif cycle_ratio >= 2.0:
        base_score = 0.75  # 평균의 2배 경과 → 높음
    elif cycle_ratio >= 1.5:
        base_score = 0.55  # 평균의 1.5배 경과 → 중상
    elif cycle_ratio >= 1.0:
        base_score = 0.35  # 평균 주기 도달 → 중간
    elif cycle_ratio >= 0.7:
        base_score = 0.20  # 70% 경과 → 낮음
    else:
        base_score = 0.10  # 최근 구매 → 매우 낮음

    # ========== 2. 보정 요인들 ==========
    adjustments = 0.0
    risk_factors = []

    # 2-1. 방문 빈도 보정 (-0.1 ~ +0.1)
    visit_freq = activity.get('visit_frequency', '중')
    if visit_freq == '높음':
        adjustments -= 0.08  # 자주 방문 → 이탈 확률 감소
    elif visit_freq == '낮음':
        adjustments += 0.08  # 방문 안함 → 이탈 확률 증가
        risk_factors.append("방문 빈도 감소")

    # 2-2. 최근 방문일 보정 (-0.05 ~ +0.1)
    last_visit = activity.get('last_visit_days_ago', 7)
    if last_visit <= 3:
        adjustments -= 0.05  # 최근 방문
    elif last_visit >= 30:
        adjustments += 0.1  # 오래 방문 안함
        risk_factors.append("30일 이상 미방문")
    elif last_visit >= 14:
        adjustments += 0.05

    # 2-3. 구매 횟수 보정 (신규 vs 충성)
    if total_purchases <= 3:
        adjustments += 0.1  # 신규 고객은 이탈 위험 높음
        risk_factors.append("구매 이력 부족")
    elif total_purchases >= 20:
        adjustments -= 0.08  # 충성 고객
    elif total_purchases >= 10:
        adjustments -= 0.04

    # 2-4. 브랜드 충성도 보정
    loyalty = brand.get('loyalty', '중')
    if loyalty == '높음':
        adjustments -= 0.08
    elif loyalty == '낮음':
        adjustments += 0.06
        risk_factors.append("브랜드 충성도 낮음")

    # 2-5. 프로모션 민감도 (양날의 검)
    discount_sensitivity = promotion.get('discount_sensitivity', '중')
    full_price_ratio = promotion.get('full_price_ratio', 0.5)

    # 프로모션 민감도 높고 정가구매 비율 낮으면 → 경쟁사 프로모션에 이탈 가능
    if discount_sensitivity == '높음' and full_price_ratio < 0.3:
        adjustments += 0.05
        risk_factors.append("할인 의존도 높음")

    # ========== 3. 특수 상황 보정 ==========

    # 구매 주기 초과 경고
    if cycle_ratio >= 1.5:
        risk_factors.append(f"구매 주기 {cycle_ratio:.1f}배 초과")
    elif cycle_ratio >= 1.0:
        risk_factors.append("구매 주기 도래")

    # ========== 4. 최종 계산 ==========
    final_probability = base_score + adjustments

    # 0~1 범위로 클램핑
    final_probability = max(0.05, min(0.95, final_probability))

    # 위험 레벨 결정
    if final_probability >= 0.6:
        risk_level = "높음"
    elif final_probability >= 0.35:
        risk_level = "중"
    else:
        risk_level = "낮음"

    return round(final_probability, 2), risk_level, risk_factors


def get_churn_details(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    이탈 확률과 함께 상세 분석 결과를 반환합니다.

    Returns:
        {
            'probability': 0.45,
            'level': '중',
            'factors': ['구매 주기 도래', '방문 빈도 감소'],
            'cycle_ratio': 1.2,
            'days_since_purchase': 42,
            'avg_interval': 35,
            'recommendation': '재구매 유도 메시지 권장'
        }
    """
    probability, level, factors = calculate_churn_probability(persona)

    purchase = persona.get('purchase', {})
    last_purchase_days = purchase.get('last_purchase_days_ago', 30)
    avg_interval = purchase.get('avg_interval', 30)

    cycle_ratio = last_purchase_days / avg_interval if avg_interval > 0 else 1.0

    # 추천 액션
    if level == "높음":
        recommendation = "🚨 즉시 이탈 방지 메시지 발송 권장"
    elif level == "중":
        if cycle_ratio >= 1.0:
            recommendation = "⚠️ 재구매 유도 또는 특별 할인 제안 권장"
        else:
            recommendation = "💡 관계 유지용 정보성 메시지 권장"
    else:
        recommendation = "✅ 정기적인 브랜드 소식 발송으로 충분"

    return {
        'probability': probability,
        'level': level,
        'factors': factors,
        'cycle_ratio': round(cycle_ratio, 2),
        'days_since_purchase': last_purchase_days,
        'avg_interval': avg_interval,
        'recommendation': recommendation
    }


def compare_churn_values(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    하드코딩된 값과 계산된 값을 비교합니다 (디버깅/검증용).
    """
    hardcoded = persona.get('risk', {}).get('churn_probability', None)
    calculated, level, factors = calculate_churn_probability(persona)

    return {
        'hardcoded': hardcoded,
        'calculated': calculated,
        'difference': round(calculated - hardcoded, 2) if hardcoded else None,
        'level': level,
        'factors': factors
    }


def get_dormancy_status(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    고객의 휴면 상태를 계산합니다.

    휴면 상태 정의:
    - 활성: 이탈확률 < 35%
    - 휴면위험: 35% ≤ 이탈확률 < 60%
    - 휴면: 이탈확률 ≥ 60%

    Returns:
        {
            'status': '활성' | '휴면위험' | '휴면',
            'status_code': 'active' | 'at_risk' | 'dormant',
            'churn_probability': 0.45,
            'color': '#28a745',
            'icon': '🟢',
            'description': '정상적인 구매 활동'
        }
    """
    probability, level, factors = calculate_churn_probability(persona)

    if probability < 0.35:
        status = "활성"
        status_code = "active"
        color = "#28a745"  # 녹색
        icon = "🟢"
        description = "정상적인 구매 활동"
    elif probability < 0.60:
        status = "휴면위험"
        status_code = "at_risk"
        color = "#ffc107"  # 노랑
        icon = "🟡"
        description = "이탈 징후 감지, 관리 필요"
    else:
        status = "휴면"
        status_code = "dormant"
        color = "#dc3545"  # 빨강
        icon = "🔴"
        description = "이탈 직전, 즉시 조치 필요"

    return {
        'status': status,
        'status_code': status_code,
        'churn_probability': probability,
        'color': color,
        'icon': icon,
        'description': description,
        'factors': factors
    }


def check_purpose_eligibility(persona: Dict[str, Any], purpose: str) -> Dict[str, Any]:
    """
    발신 목적에 대한 고객 적합성을 검증합니다.

    발신 목적별 대상 조건:
    - promotion: 활성 또는 휴면위험
    - new_product: 활성만
    - best_curation: 활성 AND 주요브랜드 ≥ 1
    - repurchase: 활성/휴면위험 AND 구매주기 ≥ 80%
    - churn_prevention: 휴면위험만
    - seasonal_gift: 활성 또는 휴면위험

    Returns:
        {
            'eligible': True/False,
            'reason': '적합 사유 또는 부적합 사유',
            'dormancy_status': '활성',
            'recommendation': '권장 발신목적'
        }
    """
    dormancy = get_dormancy_status(persona)
    status_code = dormancy['status_code']
    status = dormancy['status']

    purchase = persona.get('purchase', {})
    brand_info = persona.get('brand', {})

    last_purchase_days = purchase.get('last_purchase_days_ago', 30)
    avg_interval = purchase.get('avg_interval', 30)
    cycle_ratio = last_purchase_days / avg_interval if avg_interval > 0 else 1.0

    primary_brand = brand_info.get('primary_brand', None)
    has_primary_brand = primary_brand is not None and primary_brand != 'N/A'

    # 발신 목적별 적합성 판단
    eligibility_rules = {
        'promotion': {
            'allowed_statuses': ['active', 'at_risk'],
            'condition': lambda: True,
            'reason_ok': '프로모션에 반응할 가능성 있는 고객',
            'reason_fail': f'휴면 고객({status})은 프로모션보다 재활성화 메시지 필요'
        },
        'new_product': {
            'allowed_statuses': ['active'],
            'condition': lambda: True,
            'reason_ok': '브랜드 접점을 유지 중인 활성 고객',
            'reason_fail': f'{status} 고객에게는 신제품보다 관계 회복 메시지 우선'
        },
        'best_curation': {
            'allowed_statuses': ['active'],
            'condition': lambda: has_primary_brand,
            'reason_ok': '주요 브랜드가 있어 개인화 추천 효과적',
            'reason_fail': '주요 브랜드 없음 또는 비활성 상태'
        },
        'repurchase': {
            'allowed_statuses': ['active', 'at_risk'],
            'condition': lambda: cycle_ratio >= 0.8,
            'reason_ok': f'구매 주기 {cycle_ratio:.0%} 도래, 재구매 유도 적기',
            'reason_fail': f'구매 주기 {cycle_ratio:.0%}로 아직 여유 있음'
        },
        'churn_prevention': {
            'allowed_statuses': ['at_risk'],
            'condition': lambda: True,
            'reason_ok': '이탈 위험 고객, 휴면 방지 메시지 필요',
            'reason_fail': f'{status} 상태에서는 다른 목적이 더 적합'
        },
        'seasonal_gift': {
            'allowed_statuses': ['active', 'at_risk'],
            'condition': lambda: True,
            'reason_ok': '시즌 캠페인 대상 고객',
            'reason_fail': f'휴면 고객은 시즌보다 재활성화 우선'
        }
    }

    # 기본값 (알 수 없는 목적)
    if purpose not in eligibility_rules:
        return {
            'eligible': True,
            'reason': '일반 메시지 발송 가능',
            'dormancy_status': status,
            'recommendation': None
        }

    rule = eligibility_rules[purpose]
    status_ok = status_code in rule['allowed_statuses']
    condition_ok = rule['condition']()

    eligible = status_ok and condition_ok

    # 권장 목적 계산
    if not eligible:
        if status_code == 'dormant':
            recommendation = 'churn_prevention'
        elif status_code == 'at_risk':
            recommendation = 'churn_prevention' if cycle_ratio >= 1.0 else 'repurchase'
        else:
            recommendation = 'best_curation' if has_primary_brand else 'promotion'
    else:
        recommendation = None

    return {
        'eligible': eligible,
        'reason': rule['reason_ok'] if eligible else rule['reason_fail'],
        'dormancy_status': status,
        'dormancy_code': status_code,
        'cycle_ratio': round(cycle_ratio, 2),
        'recommendation': recommendation
    }


# 테스트용
if __name__ == "__main__":
    # 테스트 페르소나
    test_persona = {
        "name": "테스트",
        "purchase": {
            "total_count": 15,
            "last_purchase_days_ago": 75,  # 구매 주기 2배 초과
            "avg_interval": 30,
        },
        "activity": {
            "last_visit_days_ago": 20,
            "visit_frequency": "낮음"
        },
        "brand": {
            "loyalty": "중"
        },
        "promotion": {
            "discount_sensitivity": "높음",
            "full_price_ratio": 0.2
        },
        "risk": {
            "churn_probability": 0.72  # 하드코딩된 값
        }
    }

    result = get_churn_details(test_persona)
    print("=" * 50)
    print("이탈 확률 계산 결과")
    print("=" * 50)
    print(f"계산된 확률: {result['probability']:.0%}")
    print(f"위험 레벨: {result['level']}")
    print(f"구매 주기 비율: {result['cycle_ratio']:.1f}배")
    print(f"위험 요인: {', '.join(result['factors']) if result['factors'] else '없음'}")
    print(f"권장 조치: {result['recommendation']}")

    print("\n[하드코딩 값 비교]")
    compare = compare_churn_values(test_persona)
    print(f"하드코딩: {compare['hardcoded']:.0%}")
    print(f"계산값: {compare['calculated']:.0%}")
    print(f"차이: {compare['difference']:+.0%}")
