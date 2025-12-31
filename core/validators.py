# -*- coding: utf-8 -*-
"""
입력 검증 모듈
=============
페르소나, 상품, 브랜드 데이터의 유효성 검증
"""

from typing import Dict, Any, List, Optional, Tuple


class ValidationError(Exception):
    """검증 실패 예외"""
    pass


def validate_persona(persona: Dict[str, Any], raise_error: bool = False) -> Tuple[bool, List[str]]:
    """
    페르소나 데이터 검증

    필수 필드:
    - id (int)
    - display_name 또는 name (str)
    - skin_type (str)
    - concerns (list)
    - interests (list)
    - shopping_pattern (str)

    Returns:
        (is_valid, errors)
    """
    errors = []

    # 필수 필드 검증
    if not persona.get('id'):
        errors.append("id 필드 누락")

    if not persona.get('display_name') and not persona.get('name'):
        errors.append("display_name 또는 name 필드 누락")

    if not persona.get('skin_type'):
        errors.append("skin_type 필드 누락")

    concerns = persona.get('concerns')
    if not concerns or not isinstance(concerns, list):
        errors.append("concerns 필드 누락 또는 형식 오류 (list 필요)")

    interests = persona.get('interests')
    if not interests or not isinstance(interests, list):
        errors.append("interests 필드 누락 또는 형식 오류 (list 필요)")

    if not persona.get('shopping_pattern'):
        errors.append("shopping_pattern 필드 누락")

    # 선택 필드 타입 검증
    age = persona.get('age')
    if age is not None and not isinstance(age, (int, float)):
        errors.append(f"age 타입 오류: {type(age).__name__} (int 필요)")

    purchase = persona.get('purchase')
    if purchase and not isinstance(purchase, dict):
        errors.append(f"purchase 타입 오류: {type(purchase).__name__} (dict 필요)")

    is_valid = len(errors) == 0

    if raise_error and not is_valid:
        raise ValidationError(f"페르소나 검증 실패: {', '.join(errors)}")

    return is_valid, errors


def validate_product(product: Dict[str, Any], raise_error: bool = False) -> Tuple[bool, List[str]]:
    """
    상품 데이터 검증

    필수 필드:
    - id (int)
    - name (str)
    - brand (str)
    - price (int/float)
    - features (list)
    - target_skin (list)

    Returns:
        (is_valid, errors)
    """
    errors = []

    if not product.get('id'):
        errors.append("id 필드 누락")

    if not product.get('name'):
        errors.append("name 필드 누락")

    if not product.get('brand'):
        errors.append("brand 필드 누락")

    price = product.get('price')
    if price is None:
        errors.append("price 필드 누락")
    elif not isinstance(price, (int, float)):
        errors.append(f"price 타입 오류: {type(price).__name__}")
    elif price < 0:
        errors.append(f"price 음수 값: {price}")

    features = product.get('features')
    if not features or not isinstance(features, list):
        errors.append("features 필드 누락 또는 형식 오류")

    target_skin = product.get('target_skin')
    if not target_skin or not isinstance(target_skin, list):
        errors.append("target_skin 필드 누락 또는 형식 오류")

    # 할인율 검증
    discount_rate = product.get('discount_rate', 0)
    if discount_rate and not 0 <= discount_rate <= 100:
        errors.append(f"discount_rate 범위 오류: {discount_rate} (0-100 필요)")

    is_valid = len(errors) == 0

    if raise_error and not is_valid:
        raise ValidationError(f"상품 검증 실패: {', '.join(errors)}")

    return is_valid, errors


def validate_brand(brand_name: str, brand_tones: Dict[str, Any], raise_error: bool = False) -> Tuple[bool, List[str]]:
    """
    브랜드 검증

    Returns:
        (is_valid, errors)
    """
    errors = []

    if not brand_name:
        errors.append("브랜드명 누락")

    if brand_name and brand_name not in brand_tones:
        errors.append(f"알 수 없는 브랜드: {brand_name}")
        errors.append(f"사용 가능: {', '.join(brand_tones.keys())}")

    is_valid = len(errors) == 0

    if raise_error and not is_valid:
        raise ValidationError(f"브랜드 검증 실패: {', '.join(errors)}")

    return is_valid, errors


def validate_purpose(purpose: str, raise_error: bool = False) -> Tuple[bool, List[str]]:
    """
    발신목적 검증

    Returns:
        (is_valid, errors)
    """
    from config import PURPOSE_NAMES

    errors = []

    if not purpose:
        errors.append("발신목적 누락")

    # 영문 ID 또는 한글명 모두 허용
    valid_ids = set(PURPOSE_NAMES.keys())
    valid_names = set(PURPOSE_NAMES.values())

    if purpose and purpose not in valid_ids and purpose not in valid_names:
        errors.append(f"알 수 없는 발신목적: {purpose}")
        errors.append(f"사용 가능: {', '.join(valid_ids)}")

    is_valid = len(errors) == 0

    if raise_error and not is_valid:
        raise ValidationError(f"발신목적 검증 실패: {', '.join(errors)}")

    return is_valid, errors


def get_safe_persona_name(persona: Dict[str, Any], default: str = "고객") -> str:
    """
    안전하게 페르소나 이름 가져오기

    우선순위: display_name > name > default
    """
    return persona.get('display_name') or persona.get('name') or default


def get_safe_persona_field(persona: Dict[str, Any], field: str, default: Any = None) -> Any:
    """
    안전하게 페르소나 필드 가져오기

    중첩 필드도 지원: "purchase.total_count"
    """
    if '.' in field:
        parts = field.split('.')
        value = persona
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default
        return value if value is not None else default

    return persona.get(field, default)


def sanitize_html(text: str) -> str:
    """
    HTML 태그 제거 (XSS 방지)
    """
    import re
    # HTML 태그 제거
    clean = re.sub(r'<[^>]+>', '', text)
    # HTML 엔티티 이스케이프
    clean = clean.replace('&', '&amp;')
    clean = clean.replace('<', '&lt;')
    clean = clean.replace('>', '&gt;')
    clean = clean.replace('"', '&quot;')
    clean = clean.replace("'", '&#x27;')
    return clean


# 테스트
if __name__ == "__main__":
    # 테스트 페르소나
    test_persona = {
        "id": 1,
        "display_name": "민지(25세)",
        "skin_type": "복합성",
        "concerns": ["모공", "피지"],
        "interests": ["쿠션", "세럼"],
        "shopping_pattern": "가성비 중시"
    }

    is_valid, errors = validate_persona(test_persona)
    print(f"페르소나 검증: {'통과' if is_valid else '실패'}")
    if errors:
        print(f"  오류: {errors}")

    # 잘못된 페르소나
    bad_persona = {"id": 1}
    is_valid, errors = validate_persona(bad_persona)
    print(f"\n잘못된 페르소나 검증: {'통과' if is_valid else '실패'}")
    if errors:
        print(f"  오류: {errors}")

    # 안전한 필드 접근
    print(f"\n안전한 이름: {get_safe_persona_name(test_persona)}")
    print(f"안전한 이름 (없을 때): {get_safe_persona_name({})}")
