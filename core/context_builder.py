# -*- coding: utf-8 -*-
"""
발신목적별 LLM 컨텍스트 빌더
============================
Phase 3: 고객 성향 유형별 LLM 톤 지시
Phase 5: 파생 지표 기반 최적화 (토큰 88% 절감)

핵심 원칙:
- 분석/계산은 Python (무료)
- 메시지 작성만 LLM (유료)
- 파생 지표만 LLM에 전달
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.customer_analytics import (
    classify_customer_type,
    get_shopping_persona,
    calculate_discount_dependency,
    calculate_promotion_response,
    calculate_customer_value,
    calculate_repurchase_timing,
    calculate_purchase_momentum
)
from core.churn_calculator import get_dormancy_status, calculate_churn_probability
from config import PURPOSE_NAMES, calculate_model_cost, EXCHANGE_RATE


class MessageContextBuilder:
    """메시지 생성용 컨텍스트 빌더"""

    # config.py에서 가져온 발신목적 매핑 사용
    PURPOSE_NAMES = PURPOSE_NAMES

    def build(self, persona: dict, purpose: str, brand: str, products: list) -> str:
        """
        발신 목적별 최적화된 컨텍스트 생성

        Args:
            persona: 페르소나 데이터 (32개 필드)
            purpose: 발신 목적 (영문 키)
            brand: 브랜드명
            products: 추천 상품 리스트

        Returns:
            str: LLM 프롬프트용 컨텍스트 (최적화된 토큰)
        """
        purpose_name = self.PURPOSE_NAMES.get(purpose, purpose)

        # 이름에서 나이 제거: "서수진(33세)" → "서수진"
        raw_name = persona.get('name', '고객')
        if '(' in raw_name:
            customer_name = raw_name.split('(')[0].strip()
        else:
            customer_name = raw_name

        # 기본 정보 (항상 포함) - 9개 필드
        context = f"""고객 프로필:
- 이름: {customer_name}
- 나이/직업: {persona.get('age', 30)}세, {persona.get('lifestyle', '직장인')}
- 피부: {persona.get('skin_type', '복합성')} / {self._format_list(persona.get('concerns', [])[:2])}
- 관심: {self._format_list(persona.get('interests', [])[:2])}
- 패턴: {persona.get('shopping_pattern', '주기적 구매')}

발신 목적: {purpose_name}
브랜드: {brand}
"""

        # 목적별 컨텍스트 추가
        purpose_ctx = self._get_purpose_context(persona, purpose)
        if purpose_ctx:
            context += f"\n{purpose_ctx}\n"

        # 고객 성향 유형별 LLM 톤 지시 추가
        customer_type_ctx = self._get_customer_type_context(persona)
        if customer_type_ctx:
            context += f"\n{customer_type_ctx}\n"

        # 상품 정보 (최대 3개)
        context += self._format_products(products[:3])

        return context

    def _get_purpose_context(self, persona: dict, purpose: str) -> str:
        """
        발신 목적별 추가 컨텍스트 (파생 지표 기반)

        Phase 5 최적화: 원본 데이터 대신 계산된 파생 지표만 사용
        - 토큰 절감: 기존 대비 88%
        - 정보 품질: 동일 or 향상 (노이즈 제거)
        """

        if purpose == "promotion":
            # 파생 지표: 할인 의존도, 프로모션 반응
            discount = calculate_discount_dependency(persona)
            promo = calculate_promotion_response(persona)
            return f"""할인 혜택 강조:
- 할인 의존도: {discount['level']} ({discount['dependency']:.0%})
- 프로모션 반응: {promo['level']}
- 권장: {discount['recommendation']}
-> 혜택 내용 명확히, 압박 금지"""

        elif purpose == "new_product":
            # 파생 지표: 고객 유형으로 트렌드 민감도 판단
            cust_type = classify_customer_type(persona)
            is_trend = '트렌드' in cust_type['type'] or '탐색' in cust_type['type']
            return f"""신제품 트렌드:
- 고객 유형: {cust_type['type']}
- 트렌드 민감: {'높음' if is_trend else '보통'}
-> {'신제품 강조, 트렌드 키워드' if is_trend else '정보 제공 중심'}"""

        elif purpose == "best_curation":
            # 파생 지표: 고객 가치, 주 브랜드
            clv = calculate_customer_value(persona)
            brand = persona.get('brand', {}).get('primary_brand', '미정')
            return f"""프리미엄 큐레이션:
- 고객 가치: {clv['tier']} (점수 {clv['score']}/100)
- 주 브랜드: {brand}
-> 선별된 추천 강조, 할인/과장 금지"""

        elif purpose == "repurchase":
            # 파생 지표: 재구매 타이밍, 구매 모멘텀
            timing = calculate_repurchase_timing(persona)
            momentum = calculate_purchase_momentum(persona)
            return f"""재구매 리마인드:
- 타이밍: {timing['urgency']} ({timing['days_remaining']:+d}일)
- 모멘텀: {momentum['trend']} {momentum['trend_icon']}
-> '다시 찾는 분들께', 연속성 강조"""

        elif purpose == "churn_prevention":
            # 파생 지표: 휴면 상태, 이탈 확률
            dormancy = get_dormancy_status(persona)
            churn_prob, _, factors = calculate_churn_probability(persona)
            factors_text = ', '.join(factors[:2]) if factors else '없음'
            return f"""휴면 위험 대응:
- 상태: {dormancy['icon']} {dormancy['status']}
- 이탈 확률: {churn_prob:.0%}
- 위험 요인: {factors_text}
-> 부담 없는 톤, '오랜만에' 표현"""

        elif purpose == "seasonal_gift":
            # 파생 지표: 고객 가치, 선물 구매 여부
            clv = calculate_customer_value(persona)
            seasonal = persona.get('seasonal', {})
            is_gift = seasonal.get('gift_purchases', False)
            return f"""선물 맞춤 제안:
- 선물 구매: {'있음' if is_gift else '없음'}
- 고객 가치: {clv['tier']}
-> 선물 상황 제시, 포장 서비스 언급"""

        return ""

    def _get_customer_type_context(self, persona: dict) -> str:
        """고객 성향 유형별 LLM 톤 지시 (2024.01 업데이트 - 7개 페르소나 클러스터 반영)"""
        try:
            cust_type = classify_customer_type(persona)
            shop_persona = get_shopping_persona(persona)
            dormancy = get_dormancy_status(persona)

            type_code = cust_type.get('type_code', 'general')

            # 페르소나 클러스터 가져오기
            persona_cluster = persona.get('persona_cluster', '')

            # 7개 페르소나 클러스터별 LLM 톤 지시 (2024.01 업데이트)
            cluster_instructions = {
                '테크니컬 홈케어족': {
                    'tone': '전문적이고 기술적인',
                    'focus': '기술력, 효능, 피부과급 케어 강조',
                    'keywords': ['뷰티디바이스', 'LED', '갈바닉', '고기능성', '홈케어'],
                    'avoid': '가격 할인 과도 강조, 캐주얼한 표현'
                },
                '하이엔드 품격가': {
                    'tone': '고급스럽고 우아한',
                    'focus': '프리미엄, 명품, 선물, 품격 강조',
                    'keywords': ['럭셔리', '프리미엄', '한방', '선물세트', 'VIP'],
                    'avoid': '할인/특가 과도 강조, 캐주얼한 표현'
                },
                '웰니스 힐링 탐험가': {
                    'tone': '편안하고 여유로운',
                    'focus': '새로운 경험, 힐링, 라이프스타일 강조',
                    'keywords': ['웰니스', '힐링', '향기', '티', '체험'],
                    'avoid': '압박감 주는 표현, 긴급성 강조'
                },
                '연구소 기반 해결사': {
                    'tone': '전문적이고 신뢰감 있는',
                    'focus': '성분, 효능, 과학적 검증, 피부 고민 해결 강조',
                    'keywords': ['더마', '성분', '효능', '연구', '과학적'],
                    'avoid': '감성적 표현 과다, 트렌드 강조'
                },
                '트렌디 Z세대': {
                    'tone': '발랄하고 트렌디한',
                    'focus': 'SNS, 트렌드, 이벤트, 한정판 강조',
                    'keywords': ['SNS', '핫템', '신상', '이벤트', '인스타'],
                    'avoid': '격식체, 어른스러운 표현'
                },
                '합리적 큐레이터': {
                    'tone': '실용적이고 합리적인',
                    'focus': '가성비, 리뷰, 검증된 제품, 가치 강조',
                    'keywords': ['리뷰', '가성비', '베스트셀러', '검증', '합리적'],
                    'avoid': '과도한 프리미엄 강조'
                },
                '실속형 가계 수호자': {
                    'tone': '실용적이고 혜택 중심의',
                    'focus': '할인, 대용량, 사은품, 가족용 강조',
                    'keywords': ['할인', '대용량', '사은품', '가족', '알뜰'],
                    'avoid': '고가 제품 추천, 프리미엄 강조'
                }
            }

            # 쇼핑 페르소나별 추가 지시
            persona_instructions = {
                'smart_saver': '할인 혜택 명확히, 가격 대비 가치 강조',
                'beauty_intel': '성분/효능 정보 상세히, 전문적 톤',
                'pro_care': '프리미엄 서비스 언급, 전문 관리 강조',
                'home_routine': '편안한 톤, 일상 루틴 친화적',
                'genderless': '중성적 표현, 트렌디한 톤',
                'petit': '부담없는 톤, 트렌드 언급',
                'trend_scanner': '신제품/트렌드 강조, 빠른 정보',
                'steady_regular': '익숙한 제품 강조, 안정감'
            }

            shop_code = shop_persona.get('type_code', '')
            shop_instruction = persona_instructions.get(shop_code, '')

            # 휴면 상태별 추가 지시
            dormancy_instructions = {
                'active': '',
                'at_risk': '-> 부드러운 재접점, 부담 최소화',
                'dormant': '-> 환영 메시지, 복귀 혜택 강조'
            }
            dormancy_code = dormancy.get('status_code', 'active')
            dormancy_instruction = dormancy_instructions.get(dormancy_code, '')

            # 페르소나 클러스터 정보 추가
            cluster_info = cluster_instructions.get(persona_cluster, {})
            cluster_tone = cluster_info.get('tone', '')
            cluster_focus = cluster_info.get('focus', '')
            # 키워드는 모델이 어색하게 삽입하므로 제거
            cluster_avoid = cluster_info.get('avoid', '')

            context = f"""메시지 톤: {cluster_tone}
강조 포인트: {cluster_focus}
{shop_instruction}"""

            return context

        except Exception:
            # 오류 시 빈 문자열 반환
            return ""

    def _format_list(self, items: list) -> str:
        """리스트를 쉼표로 연결"""
        if not items:
            return "없음"
        return ', '.join(str(item) for item in items[:2])

    def _format_products(self, products: list) -> str:
        """상품 정보 간결하게"""
        import re
        if not products:
            return "\n추천 상품: 없음\n"

        text = "\n추천 상품:\n"
        for i, p in enumerate(products[:3], 1):
            name = p.get('name', '상품')
            # 제품명에서 숫자/용량 제거 (예: "진설크림 리치 60ml" -> "진설크림 리치")
            name = re.sub(r'\s*\d+\s*(ml|ML|g|G|매|개|입|EA)?\s*$', '', name)
            name = re.sub(r'\s*\d+\s*(ml|ML|g|G)\b', '', name)
            price = p.get('price', 0)
            discount = p.get('discount_rate', 0)

            line = f"{i}. {name} ({price:,}원)"
            if discount:
                line += f" [{discount}% 할인]"
            text += line + "\n"

        return text

    def get_token_estimate(self, context: str) -> dict:
        """토큰 수 추정"""
        # 한글 1자 ≈ 1.5 토큰, 영문/숫자 1자 ≈ 0.3 토큰
        korean_chars = sum(1 for c in context if '가' <= c <= '힣')
        other_chars = len(context) - korean_chars

        estimated_tokens = int(korean_chars * 1.5 + other_chars * 0.3)

        return {
            "char_count": len(context),
            "korean_chars": korean_chars,
            "estimated_tokens": estimated_tokens,
            "cost_gpt4o_mini": estimated_tokens * 0.15 / 1_000_000  # USD
        }

    @staticmethod
    def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> dict:
        """
        모델별 API 호출 비용 계산

        config.py의 calculate_model_cost() 래퍼
        """
        result = calculate_model_cost(model, input_tokens, output_tokens)
        result["model"] = model
        result["input_tokens"] = input_tokens
        result["output_tokens"] = output_tokens
        return result


class OptimizedContextBuilder(MessageContextBuilder):
    """
    극한 최적화 컨텍스트 빌더 (토큰 최소화)

    Phase 5: 파생 지표만 사용하여 ~140 토큰으로 압축
    - 기본 정보: 60 토큰
    - 목적별 추가: 10-18 토큰
    - 상품 정보: 30 토큰
    - 톤 지시: 20 토큰
    """

    def build_minimal(self, persona: dict, purpose: str, brand: str, products: list) -> str:
        """
        최소 토큰 컨텍스트 생성 (~140 토큰)

        사용 시점: 비용 최적화가 중요할 때
        """
        purpose_name = self.PURPOSE_NAMES.get(purpose, purpose)

        # 이름에서 나이 제거: "서수진(33세)" → "서수진"
        raw_name = persona.get('name', '고객')
        if '(' in raw_name:
            customer_name = raw_name.split('(')[0].strip()
        else:
            customer_name = raw_name

        # 파생 지표 계산 (Python - 무료)
        cust_type = classify_customer_type(persona)
        shop_persona = get_shopping_persona(persona)

        # 기본 정보 (최소)
        context = f"""고객: {customer_name}, {persona.get('age', 30)}세
피부: {persona.get('skin_type', '복합성')} / {', '.join(persona.get('concerns', [])[:2])}
유형: {cust_type['icon']} {cust_type['type']} | {shop_persona['icon']} {shop_persona['type']}

목적: {purpose_name} | 브랜드: {brand}
"""

        # 목적별 핵심 지표 (1-2줄)
        context += self._get_minimal_purpose_context(persona, purpose)

        # 상품 (최대 3개, 간결)
        if products:
            context += "\n상품: "
            context += ", ".join([f"{p.get('name', '')}({p.get('price', 0):,}원)" for p in products[:3]])

        # 톤 지시 (1줄)
        context += f"\n\n톤: {cust_type.get('llm_instruction', '').split(chr(10))[0]}"

        return context

    def _get_minimal_purpose_context(self, persona: dict, purpose: str) -> str:
        """목적별 핵심 지표 1-2줄"""

        if purpose == "promotion":
            discount = calculate_discount_dependency(persona)
            return f"할인의존: {discount['level']}({discount['dependency']:.0%}) -> {discount['recommendation']}"

        elif purpose == "new_product":
            cust_type = classify_customer_type(persona)
            return f"트렌드: {'높음' if '트렌드' in cust_type['type'] else '보통'}"

        elif purpose == "best_curation":
            clv = calculate_customer_value(persona)
            return f"가치: {clv['tier']}({clv['score']}점) -> 선별 추천"

        elif purpose == "repurchase":
            timing = calculate_repurchase_timing(persona)
            return f"타이밍: {timing['urgency']}({timing['days_remaining']:+d}일) -> 연속성 강조"

        elif purpose == "churn_prevention":
            dormancy = get_dormancy_status(persona)
            return f"상태: {dormancy['icon']}{dormancy['status']}(이탈{dormancy['churn_probability']:.0%}) -> 부담없는 톤"

        elif purpose == "seasonal_gift":
            clv = calculate_customer_value(persona)
            return f"가치: {clv['tier']} -> 선물/포장 언급"

        return ""


def test_context_builder():
    """테스트"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from data.personas import personas, products

    builder = MessageContextBuilder()
    optimized = OptimizedContextBuilder()

    print("=" * 60)
    print("Context Builder 테스트 (Phase 5 최적화)")
    print("=" * 60)

    # 각 발신목적별 테스트
    purposes = ["promotion", "repurchase", "churn_prevention"]

    for purpose in purposes:
        persona = personas[0]  # 첫 번째 페르소나

        # 기본 버전
        context = builder.build(persona, purpose, "라네즈", products[:3])
        estimate = builder.get_token_estimate(context)

        # 최적화 버전
        minimal = optimized.build_minimal(persona, purpose, "라네즈", products[:3])
        minimal_estimate = optimized.get_token_estimate(minimal)

        print(f"\n{'='*50}")
        print(f"[{builder.PURPOSE_NAMES[purpose]}]")
        print(f"{'='*50}")

        print(f"\n--- 기본 버전 ({estimate['estimated_tokens']}토큰) ---")
        print(context)

        print(f"\n--- 최적화 버전 ({minimal_estimate['estimated_tokens']}토큰) ---")
        print(minimal)

        savings = (1 - minimal_estimate['estimated_tokens'] / estimate['estimated_tokens']) * 100
        print(f"\n절감율: {savings:.0f}%")


if __name__ == "__main__":
    test_context_builder()
